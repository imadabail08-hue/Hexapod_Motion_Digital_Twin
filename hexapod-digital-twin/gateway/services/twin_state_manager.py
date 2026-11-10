"""
gateway/services/twin_state_manager.py

Authoritative central state manager for the Hexapod Digital Twin.
Coordinates all 6 state layers, operating modes, safety supervision,
Mirror-18 mapping, and health/error metrics calculation.
"""

from __future__ import annotations

import math
import time
from typing import Optional, List, Dict, Any

from gateway.models.twin_state import (
    DigitalTwinState,
    ImuRaw,
    ImuData,
    Orientation,
    PhysicalServo,
    FootPosition,
    TwinHealth,
    ConnectionStatus,
)
from gateway.models.operating_mode import ModeStateMachine, OperatingMode
from gateway.services.safety import SafetySystem
from gateway.services.kinematics import LegKinematics, DEFAULT_LEG_DIMS
from gateway.services.recorder import TelemetryRecorder
from shared.protocol.servo_map import ServoId, JOINT_CONFIG


class TwinStateManager:
    def __init__(self, safety: SafetySystem, recorder: TelemetryRecorder) -> None:
        self.safety = safety
        self.recorder = recorder
        self.mode_machine = ModeStateMachine()
        self._state = DigitalTwinState()

        # Instantiate 6 kinematics solvers for legs
        self.kinematics = [LegKinematics(*DEFAULT_LEG_DIMS) for _ in range(6)]

        self._sequence = 0
        self._last_packet_time = time.time()
        self._packet_count_window = 0
        self._last_rate_calc_time = time.time()
        self._current_hz = 0.0

        # Initial state setup
        self._update_foot_positions()

    def get_state(self) -> DigitalTwinState:
        return self._state

    def ingest_esp32_telemetry(self, packet: dict) -> None:
        """Process incoming raw telemetry from ESP32."""
        if not self.safety.validate_telemetry(packet):
            return

        self.safety.update_watchdog()
        self._sequence += 1
        self._last_packet_time = time.time()
        self._packet_count_window += 1

        # 1. RAW SENSOR STATE
        imu_dict = packet.get("imu", {})
        raw_imu = ImuRaw(
            ax=float(imu_dict.get("ax", 0.0)),
            ay=float(imu_dict.get("ay", 0.0)),
            az=float(imu_dict.get("az", 0.0)),
            gx=float(imu_dict.get("gx", 0.0)),
            gy=float(imu_dict.get("gy", 0.0)),
            gz=float(imu_dict.get("gz", 0.0)),
        )

        # 2. FILTERED STATE
        orient_dict = packet.get("orientation", {})
        orient = Orientation(
            pitch=float(orient_dict.get("pitch", 0.0)),
            roll=float(orient_dict.get("roll", 0.0)),
            yaw=float(orient_dict.get("yaw", 0.0)),
            yawAbsolute=bool(orient_dict.get("yawValid", False)),
        )

        # 3. PHYSICAL STATE
        servo_dict = packet.get("servo", {})
        phys_angle = int(servo_dict.get("physical", 90))
        phys_angle = int(self.safety.clamp_servo(phys_angle, 0))

        self._state.imu = ImuData(raw=raw_imu, filtered=raw_imu)
        self._state.orientation = orient
        self._state.physicalServo = PhysicalServo(
            id=1,
            angle=phys_angle,
            command=phys_angle,
        )

        # 4. CONTROL STATE & MODE ARBITRATION
        if self.safety.is_estop():
            self._state.emergencyStop = True
            self._apply_neutral_servos()
        elif self._state.mode in ("MIRROR_18", "LIVE_HARDWARE"):
            self.apply_mirror_18(phys_angle)

        self._state.timestamp = int(time.time() * 1000)
        self._state.sequence = self._sequence

        # Record if active
        self.recorder.record_frame(self._state)

    def apply_mirror_18(self, physical_angle: int) -> None:
        """Map 1 physical servo to 18 virtual actuators respecting kinematic limits."""
        virtuals = []
        for sid in range(18):
            cfg = JOINT_CONFIG.get(sid, {})
            direction = cfg.get("direction", 1)
            neutral_offset = cfg.get("neutral_offset", 0.0)

            # Map: visualJointAngle = direction * (servoCommand - 90) + 90 + offset
            mapped = direction * (physical_angle - 90) + 90 + neutral_offset
            clamped = self.safety.clamp_servo(mapped, sid)
            virtuals.append(round(clamped, 1))

        self._state.virtualServos = virtuals
        self._update_foot_positions()

    def _apply_neutral_servos(self) -> None:
        self._state.virtualServos = [90.0] * 18
        self._update_foot_positions()

    def apply_webots_state(self, webots_msg: dict) -> None:
        """Update simulated joint positions and orientation from Webots physics."""
        sim_joints = webots_msg.get("jointPositions", [90.0] * 18)
        self._state.simulatedServos = [float(j) for j in sim_joints]

        # Calculate servo tracking errors
        errors = []
        for i in range(18):
            v = self._state.virtualServos[i] if i < len(self._state.virtualServos) else 90.0
            s = self._state.simulatedServos[i] if i < len(self._state.simulatedServos) else 90.0
            errors.append(round(abs(v - s), 2))
        self._state.servoErrors = errors

        # Simulation RTF
        rtf = float(webots_msg.get("rtf", 1.0))
        self._state.twinHealth.simulationRTF = round(rtf, 2)

    def _update_foot_positions(self) -> None:
        """Forward kinematics for all 6 legs."""
        legs = ["LF", "RF", "LM", "RM", "LR", "RR"]
        foot_positions = []
        for i, leg in enumerate(legs):
            coxa = self._state.virtualServos[i * 3]
            femur = self._state.virtualServos[i * 3 + 1]
            tibia = self._state.virtualServos[i * 3 + 2]
            x, y, z = self.kinematics[i].forward_kinematics(coxa, femur, tibia)
            foot_positions.append(FootPosition(leg=leg, x=round(x, 4), y=round(y, 4), z=round(z, 4)))
        self._state.footPositions = foot_positions

    def update_health(self, esp32_connected: bool, webots_connected: bool, client_count: int) -> None:
        """Update connection and QoS metrics."""
        self._state.connection = ConnectionStatus(
            esp32=esp32_connected,
            webots=webots_connected,
            clientCount=client_count,
        )

        # Telemetry Frequency
        now = time.time()
        elapsed = now - self._last_rate_calc_time
        if elapsed >= 1.0:
            self._current_hz = self._packet_count_window / elapsed
            self._packet_count_window = 0
            self._last_rate_calc_time = now

        packet_age_ms = (now - self._last_packet_time) * 1000.0 if esp32_connected else 9999.0

        if not esp32_connected:
            sync_status = "SYNC_LOST"
        elif packet_age_ms < 150:
            sync_status = "SYNC_GOOD"
        elif packet_age_ms < 500:
            sync_status = "SYNC_DEGRADED"
        else:
            sync_status = "SYNC_LOST"

        max_err = max(self._state.servoErrors) if self._state.servoErrors else 0.0

        self._state.twinHealth.syncStatus = sync_status
        self._state.twinHealth.packetAgeMs = round(packet_age_ms, 1)
        self._state.twinHealth.telemetryHz = round(self._current_hz, 1)
        self._state.twinHealth.maxServoError = round(max_err, 2)
        self._state.emergencyStop = self.safety.is_estop()

    def handle_command(self, cmd: dict) -> dict:
        """Handle incoming command envelope."""
        c = cmd.get("command")
        if c == "EMERGENCY_STOP":
            self.safety.emergency_stop()
            self._apply_neutral_servos()
            return {"status": "ok", "message": "Emergency Stop Engaged"}
        elif c == "RESET_EMERGENCY_STOP":
            self.safety.reset_emergency_stop()
            return {"status": "ok", "message": "Emergency Stop Reset"}
        elif c == "SET_MODE":
            mode = cmd.get("params", {}).get("mode", "SIMULATION")
            self._state.mode = mode
            return {"status": "ok", "mode": mode}
        elif c == "ENABLE_MIRROR_18":
            self._state.mode = "MIRROR_18"
            return {"status": "ok", "mode": "MIRROR_18"}
        elif c == "START_RECORDING":
            self.recorder.start_recording()
            return {"status": "ok", "message": "Recording started"}
        elif c == "STOP_RECORDING":
            count = self.recorder.stop_recording()
            return {"status": "ok", "frames": count}
        elif c == "CENTER_SERVO":
            self.apply_mirror_18(90)
            return {"status": "ok", "message": "Servos Centered"}
        return {"status": "unknown_command", "command": c}
