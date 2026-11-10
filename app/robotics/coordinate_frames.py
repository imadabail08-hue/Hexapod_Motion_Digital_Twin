"""
app/robotics/coordinate_frames.py

Explicit coordinate frame transformations for HEX-01.
Prevents scattered sign inversions throughout the codebase.

Reference frames:
- IMU FRAME (MPU6050): X = right, Y = forward, Z = up
- ROBOT BODY FRAME:   X = forward (+X), Y = left (+Y), Z = up (+Z) (Right-Handed)
- WEBOTS FRAME:       X = right, Y = up, Z = backward (standard Webots world)
- URSINA FRAME:       X = right, Y = up, Z = forward
"""

from __future__ import annotations

import math
from typing import Tuple
from app.robotics.robot_config import LEG_MOUNT_ANGLES_DEG, get_leg_mount_position


def imu_to_body(pitch_deg: float, roll_deg: float, yaw_deg: float) -> Tuple[float, float, float]:
    """Convert MPU6050 Euler angles (degrees) into Robot Body frame.
    
    The MPU6050 is mounted flat on the center carrier board with:
    - Pitch: tilt around lateral axis
    - Roll: tilt around longitudinal axis
    - Yaw: rotation around vertical Z axis (gyro-integrated estimate)
    """
    body_pitch = pitch_deg
    body_roll  = roll_deg
    body_yaw   = yaw_deg
    return body_pitch, body_roll, body_yaw


def body_to_webots(pitch_deg: float, roll_deg: float, yaw_deg: float) -> Tuple[float, float, float]:
    """Convert body Euler angles into Webots world rotation convention."""
    webots_roll  = roll_deg
    webots_pitch = -pitch_deg
    webots_yaw   = yaw_deg
    return webots_roll, webots_pitch, webots_yaw


def body_to_ursina(pitch_deg: float, roll_deg: float, yaw_deg: float) -> Tuple[float, float, float]:
    """Convert body Euler angles into Ursina rotation tuple (X, Y, Z degrees)."""
    ursina_x = roll_deg
    ursina_y = yaw_deg
    ursina_z = pitch_deg
    return ursina_x, ursina_y, ursina_z


def leg_local_to_body(leg: str, x_local: float, y_local: float, z_local: float) -> Tuple[float, float, float]:
    """Convert a leg's local coordinate (from coxa pivot) into global body coordinates."""
    mount_x, mount_y, mount_z = get_leg_mount_position(leg)
    angle_deg = LEG_MOUNT_ANGLES_DEG.get(leg, 0.0)
    angle_rad = math.radians(angle_deg)

    # Rotate local reach vector by mount angle
    x_rot = x_local * math.cos(angle_rad) - y_local * math.sin(angle_rad)
    y_rot = x_local * math.sin(angle_rad) + y_local * math.cos(angle_rad)

    x_body = mount_x + x_rot
    y_body = mount_y + y_rot
    z_body = mount_z + z_local
    return x_body, y_body, z_body


def body_to_leg_local(leg: str, x_body: float, y_body: float, z_body: float) -> Tuple[float, float, float]:
    """Convert global body coordinate into leg local frame (relative to coxa pivot)."""
    mount_x, mount_y, mount_z = get_leg_mount_position(leg)
    dx = x_body - mount_x
    dy = y_body - mount_y
    dz = z_body - mount_z

    angle_deg = LEG_MOUNT_ANGLES_DEG.get(leg, 0.0)
    angle_rad = math.radians(-angle_deg)  # Inverse rotation

    x_local = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
    y_local = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    z_local = dz
    return x_local, y_local, z_local

