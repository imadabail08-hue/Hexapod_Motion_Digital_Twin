"""
app/twin/synchronizer.py

Central State Synchronizer & Authority Arbitrator for HEX-01.
Orchestrates:
- Hardware telemetry ingestion
- Simulation state updates from Webots
- Mirror-18 Prototype Mode mapping
- Safety limit enforcement & E-STOP latching
- Health & discrepancy calculations
"""

from __future__ import annotations

import time
from typing import Dict, Tuple, Optional
from app.twin.twin_state import DigitalTwinState, OperatingMode
from app.twin.physical_state import PhysicalHardwareState
from app.twin.simulation_state import SimulationState
from app.twin.health import TwinHealthMonitor
from app.robotics.kinematics import HexapodKinematicsEngine
from app.robotics.robot_config import (
    JOINT_NAMES,
    STAND_COXA_DEG,
    STAND_FEMUR_DEG,
    STAND_TIBIA_DEG,
    LEG_LABELS,
)


class TwinSynchronizer:
    def __init__(self):
        self.state = DigitalTwinState()
        self.kinematics = HexapodKinematicsEngine()
        self.health_monitor = TwinHealthMonitor()

        # Initial kinematic foot position calculation
        self._recompute_foot_positions()

    def get_state(self) -> DigitalTwinState:
        return self.state

    def trigger_emergency_stop(self):
        """Immediately latch emergency stop and return targets to neutral standing pose."""
        self.state.emergency_stop = True
        self._set_neutral_pose_targets()

    def reset_emergency_stop(self):
        """Reset the emergency stop latch."""
        self.state.emergency_stop = False

    def set_operating_mode(self, mode: OperatingMode) -> bool:
        """Switch operating mode with safety verification."""
        if mode == OperatingMode.LIVE_HARDWARE and not self.state.physical.esp32_connected:
            return False  # Cannot switch to live hardware without ESP32
        self.state.mode = mode
        return True

    def ingest_hardware_telemetry(self, packet: dict):
        """Process incoming raw telemetry from ESP32."""
        now = time.time()
        self.state.physical.timestamp_ms = int(now * 1000)
        self.state.physical.esp32_connected = True
        self.state.physical.packet_age_ms = 0.0

        # IMU raw
        imu = packet.get("imu", {})
        self.state.physical.imu.ax = float(imu.get("ax", 0.0))
        self.state.physical.imu.ay = float(imu.get("ay", 0.0))
        self.state.physical.imu.az = float(imu.get("az", 9.81))
        self.state.physical.imu.gx = float(imu.get("gx", 0.0))
        self.state.physical.imu.gy = float(imu.get("gy", 0.0))
        self.state.physical.imu.gz = float(imu.get("gz", 0.0))

        # Orientation
        orient = packet.get("orientation", {})
        self.state.physical.attitude.pitch_deg = float(orient.get("pitch", 0.0))
        self.state.physical.attitude.roll_deg  = float(orient.get("roll", 0.0))
        self.state.physical.attitude.yaw_deg   = float(orient.get("yaw", 0.0))

        # Physical actuator
        servo = packet.get("servo", {})
        phys_angle = int(servo.get("physical", 90))
        self.state.physical.servo.measured_angle_deg = phys_angle
        self.state.physical.servo.commanded_angle_deg = phys_angle

        # If in MIRROR_18 mode, map the 1 physical servo to all 18 virtual actuators
        if self.state.mode == OperatingMode.MIRROR_18 and not self.state.emergency_stop:
            self.apply_mirror_18_mapping(phys_angle)

        self._recompute_foot_positions()
        self._update_health_metrics()

    def apply_mirror_18_mapping(self, phys_angle_deg: int):
        """Map 1 physical servo (50-130 deg) into 18 virtual joints with correct mechanical offsets."""
        # Servo delta relative to 90 deg center:
        delta = phys_angle_deg - 90.0

        for name in JOINT_NAMES:
            if "coxa" in name:
                # Coxa stays at neutral outward angle (or slight swing)
                self.state.target_joint_angles[name] = STAND_COXA_DEG
            elif "femur" in name:
                # Femurs tilt with servo command:
                self.state.target_joint_angles[name] = round(STAND_FEMUR_DEG + delta * 0.5, 2)
            elif "tibia" in name:
                # Tibia counter-rotates to maintain stance:
                self.state.target_joint_angles[name] = round(STAND_TIBIA_DEG - delta * 0.8, 2)

    def ingest_simulation_state(self, sim_data: dict):
        """Update simulation state from Webots physics engine."""
        self.state.simulation.webots_running = True
        self.state.simulation.simulation_time_s = float(sim_data.get("simulationTime", 0.0))
        self.state.simulation.real_time_factor = float(sim_data.get("rtf", 1.0))

        sim_orient = sim_data.get("orientation", {})
        self.state.simulation.pitch_deg = float(sim_orient.get("pitch", 0.0))
        self.state.simulation.roll_deg  = float(sim_orient.get("roll", 0.0))
        self.state.simulation.yaw_deg   = float(sim_orient.get("yaw", 0.0))

        # Joint positions
        raw_positions = sim_data.get("jointPositions", [])
        for i, name in enumerate(JOINT_NAMES):
            if i < len(raw_positions):
                self.state.simulation.simulated_joint_angles[name] = float(raw_positions[i])

        # Foot contacts
        contacts = sim_data.get("footContacts", {})
        for name, val in contacts.items():
            self.state.simulation.foot_contacts[name] = bool(val)

        self._update_health_metrics()

    def _set_neutral_pose_targets(self):
        for name in JOINT_NAMES:
            if "coxa" in name:
                self.state.target_joint_angles[name] = STAND_COXA_DEG
            elif "femur" in name:
                self.state.target_joint_angles[name] = STAND_FEMUR_DEG
            elif "tibia" in name:
                self.state.target_joint_angles[name] = STAND_TIBIA_DEG

    def _recompute_foot_positions(self):
        leg_angles = {}
        for leg in LEG_LABELS:
            prefix = leg.lower()
            c = self.state.target_joint_angles.get(f"{prefix}_coxa", STAND_COXA_DEG)
            f = self.state.target_joint_angles.get(f"{prefix}_femur", STAND_FEMUR_DEG)
            t = self.state.target_joint_angles.get(f"{prefix}_tibia", STAND_TIBIA_DEG)
            leg_angles[leg] = (c, f, t)
        self.state.foot_positions_body_frame = self.kinematics.compute_all_foot_positions_body_frame(leg_angles)

    def _update_health_metrics(self):
        self.state.health = self.health_monitor.evaluate_health(
            esp32_connected=self.state.physical.esp32_connected,
            packet_age_ms=self.state.physical.packet_age_ms,
            telemetry_hz=self.state.physical.telemetry_rate_hz,
            latency_ms=0.0,
            sim_rtf=self.state.simulation.real_time_factor,
            target_joints=self.state.target_joint_angles,
            actual_joints=self.state.simulation.simulated_joint_angles,
            phys_pitch=self.state.physical.attitude.pitch_deg,
            sim_pitch=self.state.simulation.pitch_deg,
            phys_roll=self.state.physical.attitude.roll_deg,
            sim_roll=self.state.simulation.roll_deg,
            phys_yaw=self.state.physical.attitude.yaw_deg,
            sim_yaw=self.state.simulation.yaw_deg,
        )

