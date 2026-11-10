"""
app/twin/physical_state.py

Represents the physical hardware state of the robot (ESP32, MPU6050, MG90S).
Strictly decoupled from simulation or visualization states.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ImuMeasurement:
    ax: float = 0.0
    ay: float = 0.0
    az: float = 9.81
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0
    temp_c: float = 25.0


@dataclass
class BodyAttitude:
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    yaw_deg: float = 0.0
    yaw_is_absolute: bool = False  # False for MPU6050 (drift expected)
    pitch_zero_offset: float = 0.0
    roll_zero_offset: float = 0.0
    gyro_bias_y: float = 0.0
    is_calibrated: bool = False


@dataclass
class PhysicalActuatorState:
    servo_id: int = 1
    gpio_pin: int = 25
    measured_angle_deg: int = 90
    commanded_angle_deg: int = 90
    min_safe_deg: int = 50
    max_safe_deg: int = 130


@dataclass
class PhysicalHardwareState:
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    esp32_connected: bool = False
    mpu6050_active: bool = False
    imu: ImuMeasurement = field(default_factory=ImuMeasurement)
    attitude: BodyAttitude = field(default_factory=BodyAttitude)
    servo: PhysicalActuatorState = field(default_factory=PhysicalActuatorState)
    packet_sequence: int = 0
    packet_age_ms: float = 9999.0
    telemetry_rate_hz: float = 0.0

