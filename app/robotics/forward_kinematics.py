"""
app/robotics/forward_kinematics.py

Analytical 3-DOF Forward Kinematics for a hexapod leg.
Calculates foot tip position (x, y, z) in meters relative to coxa joint origin.
"""

from __future__ import annotations

import math
from typing import Tuple
from app.robotics.robot_config import DEFAULT_COXA_LEN, DEFAULT_FEMUR_LEN, DEFAULT_TIBIA_LEN


def forward_kinematics_3dof(
    coxa_deg: float,
    femur_deg: float,
    tibia_deg: float,
    coxa_len: float = DEFAULT_COXA_LEN,
    femur_len: float = DEFAULT_FEMUR_LEN,
    tibia_len: float = DEFAULT_TIBIA_LEN,
) -> Tuple[float, float, float]:
    """Compute local foot position from joint angles (degrees).
    
    Convention:
    - Coxa rotates around local Z (horizontal yaw swing).
    - Femur rotates around local Y/X (vertical lift). Positive femur raises the knee.
    - Tibia rotates around local Y/X (knee extension). Negative tibia bends knee downward.
    """
    coxa_rad  = math.radians(coxa_deg)
    femur_rad = math.radians(femur_deg)
    tibia_rad = math.radians(tibia_deg)

    # 2D projection in the leg's sagittal plane
    # Cumulative angle for the tibia link:
    theta_knee = femur_rad + tibia_rad

    # Radial reach in the horizontal plane from the coxa pivot
    horizontal_reach = coxa_len + femur_len * math.cos(femur_rad) + tibia_len * math.cos(theta_knee)

    # Vertical height Z (relative to coxa pivot)
    z = femur_len * math.sin(femur_rad) + tibia_len * math.sin(theta_knee)

    # Project horizontal reach using coxa yaw rotation
    x = horizontal_reach * math.cos(coxa_rad)
    y = horizontal_reach * math.sin(coxa_rad)

    return x, y, z

