"""
Hexapod Digital Twin — Webots Controller
=========================================
Synchronizes Webots physics simulation with the Python Gateway.

Protocol
--------
- Listens for TCP JSON commands from Gateway on port 8766
- Sends JSON state snapshots to Gateway at 20 Hz
- Motor positions are stored internally in radians; the wire
  protocol uses degrees in the range [0, 180] to match the
  physical servo convention used by the ESP32.

Coordinate convention
---------------------
- Servo 0° → -π/2 rad (full retract)
- Servo 90° → 0 rad (neutral / centre)
- Servo 180° → +π/2 rad (full extend)
"""

from controller import Robot  # Webots built-in
import socket
import json
import time
import math

# ------------------------------------------------------------------
# Joint and sensor name tables
# ------------------------------------------------------------------
JOINT_NAMES = [
    "lf_coxa",  "lf_femur",  "lf_tibia",
    "lm_coxa",  "lm_femur",  "lm_tibia",
    "lr_coxa",  "lr_femur",  "lr_tibia",
    "rf_coxa",  "rf_femur",  "rf_tibia",
    "rm_coxa",  "rm_femur",  "rm_tibia",
    "rr_coxa",  "rr_femur",  "rr_tibia",
]

FOOT_SENSORS = ["lf_foot", "lm_foot", "lr_foot", "rf_foot", "rm_foot", "rr_foot"]


# ------------------------------------------------------------------
# Controller class
# ------------------------------------------------------------------
class HexapodTwinController:
    """
    Main Webots controller for the Hexapod Digital Twin.

    Responsibilities
    ----------------
    1. Enumerate and enable all 18 motors + position sensors.
    2. Enable all 6 foot TouchSensors.
    3. Enable IMU, Gyro, and Accelerometer.
    4. Maintain a non-blocking TCP connection to the Gateway.
    5. Read sensor data each timestep and broadcast state at 20 Hz.
    6. Receive motor commands from the Gateway and apply them.
    7. Honour emergency-stop flag.
    """

    def __init__(self):
        # --- Webots robot handle ----------------------------------------
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())  # 8 ms

        # --- Motors and position sensors --------------------------------
        self.motors = {}
        self.sensors = {}
        for name in JOINT_NAMES:
            motor = self.robot.getDevice(name)
            if motor is None:
                print(f"[WEBOTS] WARNING: motor '{name}' not found in world!")
                continue
            motor.setPosition(0.0)   # neutral (0 rad == servo 90°)
            motor.setVelocity(1.0)
            self.motors[name] = motor

            sensor = self.robot.getDevice(name + "_sensor")
            if sensor is not None:
                sensor.enable(self.timestep)
            self.sensors[name] = sensor

        # --- Foot touch sensors -----------------------------------------
        self.touch_sensors = {}
        for name in FOOT_SENSORS:
            ts = self.robot.getDevice(name)
            if ts is not None:
                ts.enable(self.timestep)
                self.touch_sensors[name] = ts
            else:
                print(f"[WEBOTS] WARNING: touch sensor '{name}' not found!")

        # --- IMU devices ------------------------------------------------
        self.imu = self.robot.getDevice("imu")
        if self.imu:
            self.imu.enable(self.timestep)

        self.gyro = self.robot.getDevice("gyro")
        if self.gyro:
            self.gyro.enable(self.timestep)

        self.accel = self.robot.getDevice("accelerometer")
        if self.accel:
            self.accel.enable(self.timestep)

        # --- Gateway TCP connection ------------------------------------
        self.gateway_host = "127.0.0.1"
        self.gateway_port = 8766
        self.sock = None
        self._recv_buf = b""
        self.connect_to_gateway()

        # --- Controller state ------------------------------------------
        self.servo_targets = [90.0] * 18  # degrees, [0..180]
        self.emergency_stop = False
        self.sim_start_time = time.time()

        print(f"[WEBOTS] Controller initialised — timestep={self.timestep}ms")

    # ------------------------------------------------------------------
    # Network helpers
    # ------------------------------------------------------------------

    def connect_to_gateway(self):
        """Non-blocking TCP connection attempt to Gateway."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            err = self.sock.connect_ex((self.gateway_host, self.gateway_port))
            # connect_ex returns EINPROGRESS / WSAEWOULDBLOCK on non-blocking —
            # that is expected and harmless.
            print(
                f"[WEBOTS] Connecting to gateway "
                f"{self.gateway_host}:{self.gateway_port} (err={err})"
            )
        except Exception as exc:
            print(f"[WEBOTS] Gateway connection failed: {exc}")
            self.sock = None

    def receive_commands(self):
        """
        Non-blocking receive from Gateway.
        Handles newline-delimited JSON (NDJSON).
        Multiple messages may arrive in a single recv call.
        """
        if self.sock is None:
            return
        try:
            chunk = self.sock.recv(4096)
            if not chunk:
                # Connection closed by remote
                print("[WEBOTS] Gateway closed connection — will reconnect.")
                self.sock = None
                return
            self._recv_buf += chunk
        except BlockingIOError:
            pass  # No data available right now — normal
        except OSError as exc:
            print(f"[WEBOTS] Receive error: {exc}")
            self.sock = None
            return

        # Process all complete lines
        while b"\n" in self._recv_buf:
            line, self._recv_buf = self._recv_buf.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
                self._handle_command(msg)
            except json.JSONDecodeError as exc:
                print(f"[WEBOTS] Bad JSON from gateway: {exc}")

    def _handle_command(self, msg: dict):
        """Dispatch a parsed command dict."""
        msg_type = msg.get("type", "")
        if msg_type == "control":
            self.servo_targets = msg.get("servoTargets", [90.0] * 18)
            self.emergency_stop = msg.get("emergencyStop", False)
            if self.emergency_stop:
                print("[WEBOTS] ⚠  EMERGENCY STOP received!")
        elif msg_type == "ping":
            # Respond immediately with pong (best-effort)
            self.send_raw({"type": "pong", "ts": int(time.time() * 1000)})
        else:
            print(f"[WEBOTS] Unknown message type: '{msg_type}'")

    def send_raw(self, obj: dict):
        """Send a JSON dict as a newline-terminated string."""
        if self.sock is None:
            return
        try:
            data = (json.dumps(obj) + "\n").encode("utf-8")
            self.sock.sendall(data)
        except Exception as exc:
            print(f"[WEBOTS] Send error: {exc}")
            self.sock = None

    # ------------------------------------------------------------------
    # Sensor reading
    # ------------------------------------------------------------------

    def get_simulated_state(self) -> dict:
        """
        Read all enabled sensors and return a dictionary
        conforming to the DigitalTwinState wire format.
        """
        # IMU orientation (roll, pitch, yaw in radians)
        if self.imu:
            rpy = self.imu.getRollPitchYaw()
            roll_deg  = math.degrees(rpy[0])
            pitch_deg = math.degrees(rpy[1])
            yaw_deg   = math.degrees(rpy[2])
        else:
            roll_deg = pitch_deg = yaw_deg = 0.0

        # Gyro (rad/s)
        if self.gyro:
            gyro_xyz = list(self.gyro.getValues())
        else:
            gyro_xyz = [0.0, 0.0, 0.0]

        # Accelerometer (m/s²)
        if self.accel:
            accel_xyz = list(self.accel.getValues())
        else:
            accel_xyz = [0.0, 0.0, 9.81]

        # Joint positions — convert radians to degrees [0..180]
        joint_positions = []
        for name in JOINT_NAMES:
            sensor = self.sensors.get(name)
            if sensor is not None:
                angle_rad = sensor.getValue()
                # Convert: 0 rad → 90°, +π/2 → 180°, -π/2 → 0°
                angle_deg = math.degrees(angle_rad) + 90.0
            else:
                angle_deg = 90.0
            joint_positions.append(round(angle_deg, 2))

        # Foot contacts
        foot_contacts = {}
        for name, ts in self.touch_sensors.items():
            foot_contacts[name] = bool(ts.getValue() > 0)

        # Timing / real-time factor
        sim_time  = self.robot.getTime()
        wall_time = time.time() - self.sim_start_time
        rtf       = sim_time / wall_time if wall_time > 0 else 1.0

        return {
            "type": "simulated_state",
            "timestamp": int(time.time() * 1000),
            "orientation": {
                "roll":  round(roll_deg,  3),
                "pitch": round(pitch_deg, 3),
                "yaw":   round(yaw_deg,   3),
            },
            "imu": {
                "ax": round(accel_xyz[0], 4),
                "ay": round(accel_xyz[1], 4),
                "az": round(accel_xyz[2], 4),
                "gx": round(math.degrees(gyro_xyz[0]), 4),
                "gy": round(math.degrees(gyro_xyz[1]), 4),
                "gz": round(math.degrees(gyro_xyz[2]), 4),
            },
            "jointPositions":  joint_positions,
            "servoTargets":    list(self.servo_targets),
            "footContacts":    foot_contacts,
            "emergencyStop":   self.emergency_stop,
            "simulationTime":  round(sim_time, 4),
            "rtf":             round(rtf, 4),
        }

    # ------------------------------------------------------------------
    # Motor control
    # ------------------------------------------------------------------

    def apply_servo_targets(self, targets: list):
        """
        Apply servo targets to Webots motors.

        Parameters
        ----------
        targets : list[float]
            18 angles in degrees, expected range [0, 180].
            90° = neutral / centre position.
        """
        if self.emergency_stop:
            # Drive all joints to neutral safe position
            for motor in self.motors.values():
                motor.setPosition(0.0)
            return

        for i, name in enumerate(JOINT_NAMES):
            motor = self.motors.get(name)
            if motor is None:
                continue
            if i < len(targets):
                raw_deg   = float(targets[i])
                # Convert degree [0..180] → radian [-π/2..+π/2]
                angle_rad = math.radians(raw_deg - 90.0)
                # Clamp to safe motor limits
                angle_rad = max(-1.5708, min(1.5708, angle_rad))
                motor.setPosition(angle_rad)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Main Webots control loop — called once, runs until sim ends."""
        print("[WEBOTS] Twin controller running…")
        last_send_time = 0.0     # simulation time of last state broadcast

        while self.robot.step(self.timestep) != -1:
            current_sim_time = self.robot.getTime()

            # 1. Receive any pending commands from Gateway
            self.receive_commands()

            # 2. If disconnected, attempt periodic reconnect (every 5 s wall-clock)
            if self.sock is None:
                wall_elapsed = time.time() - self.sim_start_time
                if int(wall_elapsed) % 5 == 0:
                    self.connect_to_gateway()

            # 3. Apply latest motor targets
            self.apply_servo_targets(self.servo_targets)

            # 4. Broadcast state at ~20 Hz (every 0.05 sim-seconds)
            if current_sim_time - last_send_time >= 0.05:
                state = self.get_simulated_state()
                self.send_raw(state)
                last_send_time = current_sim_time

        print("[WEBOTS] Simulation ended — controller exiting.")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
controller = HexapodTwinController()
controller.run()
