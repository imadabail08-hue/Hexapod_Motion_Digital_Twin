"""
app/twin/health.py

Digital Twin Synchronization Quality-of-Service and Health Monitor.
Computes discrepancies between physical hardware and physics simulation,
packet age, tracking error, latency, and overall sync status.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TwinHealthReport:
    sync_status: str = "LOST"               # "GOOD", "DEGRADED", "LOST"
    packet_age_ms: float = 9999.0
    latency_ms: float = 0.0
    telemetry_hz: float = 0.0
    packet_loss_pct: float = 0.0

    # Tracking error metrics (degrees)
    max_servo_error_deg: float = 0.0
    rms_servo_error_deg: float = 0.0
    orientation_error_pitch: float = 0.0
    orientation_error_roll: float = 0.0
    orientation_error_yaw: float = 0.0

    # Webots physics real-time factor
    simulation_rtf: float = 1.0


class TwinHealthMonitor:
    def __init__(self, good_thresh_ms: float = 150.0, degraded_thresh_ms: float = 500.0):
        self.good_thresh_ms = good_thresh_ms
        self.degraded_thresh_ms = degraded_thresh_ms

    def evaluate_health(
        self,
        esp32_connected: bool,
        packet_age_ms: float,
        telemetry_hz: float,
        latency_ms: float,
        sim_rtf: float,
        target_joints: Dict[str, float],
        actual_joints: Dict[str, float],
        phys_pitch: float,
        sim_pitch: float,
        phys_roll: float,
        sim_roll: float,
        phys_yaw: float,
        sim_yaw: float,
    ) -> TwinHealthReport:
        """Evaluate twin QoS and return a comprehensive TwinHealthReport."""
        # 1. Synchronization quality
        if not esp32_connected:
            sync_status = "LOST"
        elif packet_age_ms < self.good_thresh_ms:
            sync_status = "GOOD"
        elif packet_age_ms < self.degraded_thresh_ms:
            sync_status = "DEGRADED"
        else:
            sync_status = "LOST"

        # 2. Servo tracking errors
        errors = []
        for name, target in target_joints.items():
            if name in actual_joints:
                err = abs(target - actual_joints[name])
                errors.append(err)

        max_err = max(errors) if errors else 0.0
        rms_err = math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0

        # 3. Orientation discrepancy (physical vs simulation)
        err_pitch = abs(phys_pitch - sim_pitch) if esp32_connected else 0.0
        err_roll  = abs(phys_roll - sim_roll) if esp32_connected else 0.0
        err_yaw   = abs(phys_yaw - sim_yaw) if esp32_connected else 0.0

        return TwinHealthReport(
            sync_status=sync_status,
            packet_age_ms=round(packet_age_ms, 1),
            latency_ms=round(latency_ms, 1),
            telemetry_hz=round(telemetry_hz, 1),
            packet_loss_pct=0.0,
            max_servo_error_deg=round(max_err, 2),
            rms_servo_error_deg=round(rms_err, 2),
            orientation_error_pitch=round(err_pitch, 2),
            orientation_error_roll=round(err_roll, 2),
            orientation_error_yaw=round(err_yaw, 2),
            simulation_rtf=round(sim_rtf, 2),
        )

