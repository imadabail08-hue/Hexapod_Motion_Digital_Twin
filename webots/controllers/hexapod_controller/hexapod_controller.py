"""
hexapod_controller.py

Webots physics controller for HEX-01 Industrial Hexapod Digital Twin.
Initializes 18 articulated joint motors, 18 position sensors, 6 foot contact sensors,
IMU/Gyro/Accelerometer, engages the POSE_NEUTRAL_STAND posture, and streams physics state.
"""

import math
import time
import socket
import json
import sys

try:
    from controller import Robot
except ImportError:
    # Allows offline linting/testing without Webots environment
    Robot = None

JOINT_NAMES = [
    "lf_coxa", "lf_femur", "lf_tibia",
    "lm_coxa", "lm_femur", "lm_tibia",
    "lr_coxa", "lr_femur", "lr_tibia",
    "rf_coxa", "rf_femur", "rf_tibia",
    "rm_coxa", "rm_femur", "rm_tibia",
    "rr_coxa", "rr_femur", "rr_tibia",
]

FOOT_SENSORS = [
    "lf_foot", "lm_foot", "lr_foot",
    "rf_foot", "rm_foot", "rr_foot"
]

# ------------------------------------------------------------------------------
# POSE_NEUTRAL_STAND (radians): Coxa = 0.0, Femur = +0.4189 rad (+24 deg), Tibia = -1.1868 rad (-68 deg)
# ------------------------------------------------------------------------------
STAND_FEMUR_RAD = math.radians(24.0)
STAND_TIBIA_RAD = math.radians(-68.0)
STAND_COXA_RAD  = math.radians(0.0)

NEUTRAL_STAND_TARGETS_RAD = [
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # LF
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # LM
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # LR
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # RF
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # RM
    STAND_COXA_RAD, STAND_FEMUR_RAD, STAND_TIBIA_RAD,  # RR
]


class HexapodWebotsController:
    def __init__(self):
        if Robot is None:
            print("[WARN] Webots controller library not found in Python path.")
            return

        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())

        self.motors = {}
        self.sensors = {}
        for name in JOINT_NAMES:
            motor = self.robot.getDevice(name)
            if motor:
                motor.setVelocity(4.0)
                self.motors[name] = motor

            sensor = self.robot.getDevice(name + "_sensor")
            if sensor:
                sensor.enable(self.timestep)
                self.sensors[name] = sensor

        self.feet = {}
        for name in FOOT_SENSORS:
            ts = self.robot.getDevice(name)
            if ts:
                ts.enable(self.timestep)
                self.feet[name] = ts

        self.imu = self.robot.getDevice("imu")
        if self.imu:
            self.imu.enable(self.timestep)

        self.gyro = self.robot.getDevice("gyro")
        if self.gyro:
            self.gyro.enable(self.timestep)

        self.accel = self.robot.getDevice("accelerometer")
        if self.accel:
            self.accel.enable(self.timestep)

        # Gateway TCP socket (8766)
        self.gateway_host = "127.0.0.1"
        self.gateway_port = 8766
        self.sock = None
        self._connect_gateway()

        # Engage POSE_NEUTRAL_STAND immediately
        self.apply_joint_targets_rad(NEUTRAL_STAND_TARGETS_RAD)
        print(f"[HEX-01] Controller initialized. 18 joints active in POSE_NEUTRAL_STAND.")

    def _connect_gateway(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            self.sock.connect_ex((self.gateway_host, self.gateway_port))
        except Exception:
            self.sock = None

    def apply_joint_targets_rad(self, targets_rad):
        for i, name in enumerate(JOINT_NAMES):
            if name in self.motors and i < len(targets_rad):
                self.motors[name].setPosition(float(targets_rad[i]))

    def read_simulated_state(self):
        joint_positions_deg = []
        for name in JOINT_NAMES:
            if name in self.sensors:
                val_rad = self.sensors[name].getValue()
                joint_positions_deg.append(round(math.degrees(val_rad), 2))
            else:
                joint_positions_deg.append(0.0)

        contacts = {}
        for name in FOOT_SENSORS:
            if name in self.feet:
                contacts[name] = self.feet[name].getValue() > 0.05
            else:
                contacts[name] = False

        rpy = [0.0, 0.0, 0.0]
        if self.imu:
            rpy = self.imu.getRollPitchYaw()

        return {
            "type": "simulated_state",
            "timestamp": int(time.time() * 1000),
            "orientation": {
                "roll": round(math.degrees(rpy[0]), 2),
                "pitch": round(math.degrees(rpy[1]), 2),
                "yaw": round(math.degrees(rpy[2]), 2),
            },
            "jointPositions": joint_positions_deg,
            "footContacts": contacts,
            "simulationTime": round(self.robot.getTime(), 3),
            "rtf": 1.0,
        }

    def sync_network(self, state):
        if not self.sock:
            self._connect_gateway()
            return

        # Send state
        try:
            payload = json.dumps(state) + "\n"
            self.sock.sendall(payload.encode("utf-8"))
        except Exception:
            self.sock = None
            return

        # Receive commands
        try:
            data = self.sock.recv(4096)
            if data:
                cmd = json.loads(data.decode("utf-8").strip())
                if cmd.get("type") == "control":
                    targets_deg = cmd.get("servoTargets", [])
                    targets_rad = [math.radians(t - 90.0) for t in targets_deg]
                    self.apply_joint_targets_rad(targets_rad)
        except BlockingIOError:
            pass
        except Exception:
            self.sock = None

    def run(self):
        last_sync = 0.0
        while self.robot.step(self.timestep) != -1:
            t = self.robot.getTime()
            if t - last_sync >= 0.02:  # 50 Hz
                state = self.read_simulated_state()
                self.sync_network(state)
                last_sync = t


if __name__ == "__main__":
    if Robot is not None:
        controller = HexapodWebotsController()
        controller.run()
