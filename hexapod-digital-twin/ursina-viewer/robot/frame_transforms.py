"""
Coordinate frame transformation functions.
Converts between IMU, Robot, Three.js, Ursina, and Webots frames.

IMU FRAME   (MPU6050): X=right, Y=forward, Z=up
ROBOT FRAME: X=forward, Y=left, Z=up
WEBOTS FRAME: X=right, Y=up, Z=backward (RHR)
THREE.JS FRAME: X=right, Y=up, Z=toward viewer
URSINA FRAME: X=right, Y=up, Z=toward viewer
"""
from typing import Tuple

def imu_to_robot(pitch: float, roll: float, yaw: float) -> Tuple[float, float, float]:
    """Convert IMU Euler angles to Robot Body frame."""
    return pitch, roll, yaw

def robot_to_webots(pitch: float, roll: float, yaw: float) -> Tuple[float, float, float]:
    """Convert Robot Body frame to Webots world frame."""
    webots_roll = roll
    webots_pitch = -pitch
    webots_yaw = yaw
    return webots_roll, webots_pitch, webots_yaw

def robot_to_threejs(pitch: float, roll: float, yaw: float) -> Tuple[float, float, float]:
    """Convert Robot Body frame to Three.js frame (degrees)."""
    threejs_x = -roll
    threejs_y = yaw
    threejs_z = -pitch
    return threejs_x, threejs_y, threejs_z

def imu_to_ursina(pitch: float, roll: float, yaw: float) -> Tuple[float, float, float]:
    """Convert IMU angles to Ursina rotation_xyz (degrees)."""
    ursina_x = roll
    ursina_y = yaw
    ursina_z = pitch
    return ursina_x, ursina_y, ursina_z

def robot_to_ursina(pitch: float, roll: float, yaw: float) -> Tuple[float, float, float]:
    """Convert Robot Body frame to Ursina rotation."""
    r, p, y = imu_to_robot(pitch, roll, yaw)
    return imu_to_ursina(r, p, y)
