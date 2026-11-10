"""
app/robotics/inverse_kinematics.py

Analytical 3-DOF Geometric Inverse Kinematics for a hexapod leg.
Given a desired foot target (x, y, z) in meters relative to coxa joint origin,
computes (coxa_deg, femur_deg, tibia_deg) or returns None if unreachable.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple
from app.robotics.robot_config import (
    DEFAULT_COXA_LEN,
    DEFAULT_FEMUR_LEN,
    DEFAULT_TIBIA_LEN,
    JOINT_LIMITS_DEG,
)


def _safe_acos(v: float) -> float:
    """Clamp float to [-1.0, 1.0] to prevent math domain error due to floating point precision."""
    return math.acos(max(-1.0, min(1.0, v)))


def inverse_kinematics_3dof(
    target_x: float,
    target_y: float,
    target_z: float,
    coxa_len: float = DEFAULT_COXA_LEN,
    femur_len: float = DEFAULT_FEMUR_LEN,
    tibia_len: float = DEFAULT_TIBIA_LEN,
    enforce_limits: bool = True,
) -> Optional[Tuple[float, float, float]]:
    """Solve closed-form geometric IK for one 3-DOF leg.
    
    Returns (coxa_deg, femur_deg, tibia_deg) or None if target is outside mechanical workspace.
    """
    # 1. Coxa yaw angle (in horizontal plane)
    coxa_rad = math.atan2(target_y, target_x)
    coxa_deg = math.degrees(coxa_rad)

    # 2. Horizontal reach from femur pivot
    planar_dist = math.sqrt(target_x * target_x + target_y * target_y)
    femur_to_foot_horiz = planar_dist - coxa_len

    if femur_to_foot_horiz < 0.0:
        # Target is inside the coxa radius
        return None

    # 3. Direct distance from femur pivot to foot tip
    d = math.sqrt(femur_to_foot_horiz * femur_to_foot_horiz + target_z * target_z)

    # Reachability checks
    max_reach = femur_len + tibia_len
    min_reach = abs(femur_len - tibia_len)

    if d > max_reach or d < min_reach or d == 0.0:
        return None

    # 4. Law of Cosines for knee (tibia) angle
    cos_tibia = (femur_len * femur_len + tibia_len * tibia_len - d * d) / (2.0 * femur_len * tibia_len)
    # Knee interior angle
    beta = _safe_acos(cos_tibia)
    # In our coordinate system, neutral is straight (180 deg) and bending down is negative:
    tibia_rad = beta - math.pi
    tibia_deg = math.degrees(tibia_rad)

    # 5. Femur angle
    alpha_1 = math.atan2(target_z, femur_to_foot_horiz)
    cos_alpha_2 = (femur_len * femur_len + d * d - tibia_len * tibia_len) / (2.0 * femur_len * d)
    alpha_2 = _safe_acos(cos_alpha_2)
    femur_rad = alpha_1 + alpha_2
    femur_deg = math.degrees(femur_rad)

    # 6. Optional limit checks
    if enforce_limits:
        c_min, c_max = JOINT_LIMITS_DEG["coxa"]
        f_min, f_max = JOINT_LIMITS_DEG["femur"]
        t_min, t_max = JOINT_LIMITS_DEG["tibia"]

        if not (c_min <= coxa_deg <= c_max):
            return None
        if not (f_min <= femur_deg <= f_max):
            return None
        if not (t_min <= tibia_deg <= t_max):
            return None

    return round(coxa_deg, 2), round(femur_deg, 2), round(tibia_deg, 2)

