"""
app/robotics/robot_config.py

Central mechanical & kinematic configuration for HEX-01.
Reads config/robot_physics.yaml when available, or provides robust default constants.
All values marked [ESTIMATED PARAMETERS] are realistic engineering estimates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Any

# ------------------------------------------------------------------------------
# Default Dimensions & Masses [ESTIMATED PARAMETERS]
# ------------------------------------------------------------------------------
DEFAULT_BODY_RADIUS = 0.110       # 110 mm
DEFAULT_BODY_HEIGHT = 0.042       # 42 mm
DEFAULT_COXA_LEN    = 0.052       # 52 mm
DEFAULT_FEMUR_LEN   = 0.075       # 75 mm
DEFAULT_TIBIA_LEN   = 0.125       # 125 mm
DEFAULT_FOOT_RADIUS = 0.012       # 12 mm

# ------------------------------------------------------------------------------
# POSE_NEUTRAL_STAND: Stance angles for firm ground contact at Z = 0
# ------------------------------------------------------------------------------
STAND_COXA_DEG  = 0.0
STAND_FEMUR_DEG = 24.0
STAND_TIBIA_DEG = -68.0

STAND_CLEARANCE_HEIGHT_M = 0.095  # 95 mm above ground plane

# ------------------------------------------------------------------------------
# 6 Legs: Mount angles around body center (Z-axis)
# ------------------------------------------------------------------------------
LEG_MOUNT_ANGLES_DEG: Dict[str, float] = {
    "LF":  45.0,   # Left Front
    "LM":  90.0,   # Left Middle
    "LR": 135.0,   # Left Rear
    "RF": -45.0,   # Right Front
    "RM": -90.0,   # Right Middle
    "RR": -135.0,  # Right Rear
}

LEG_LABELS: List[str] = ["LF", "LM", "LR", "RF", "RM", "RR"]

# Canonical 18 Joint Names in sequential order
JOINT_NAMES: List[str] = [
    "lf_coxa", "lf_femur", "lf_tibia",
    "lm_coxa", "lm_femur", "lm_tibia",
    "lr_coxa", "lr_femur", "lr_tibia",
    "rf_coxa", "rf_femur", "rf_tibia",
    "rm_coxa", "rm_femur", "rm_tibia",
    "rr_coxa", "rr_femur", "rr_tibia",
]

FOOT_SENSOR_NAMES: List[str] = [
    "lf_foot", "lm_foot", "lr_foot",
    "rf_foot", "rm_foot", "rr_foot",
]

# Joint angular limits (degrees)
JOINT_LIMITS_DEG: Dict[str, Tuple[float, float]] = {
    "coxa":  (-60.0,  60.0),
    "femur": (-75.0,  75.0),
    "tibia": (-120.0, 15.0),
}


@dataclass
class HexapodDimensions:
    body_radius: float = DEFAULT_BODY_RADIUS
    body_height: float = DEFAULT_BODY_HEIGHT
    coxa_len: float = DEFAULT_COXA_LEN
    femur_len: float = DEFAULT_FEMUR_LEN
    tibia_len: float = DEFAULT_TIBIA_LEN
    foot_radius: float = DEFAULT_FOOT_RADIUS
    clearance_height: float = STAND_CLEARANCE_HEIGHT_M


def get_leg_mount_position(leg: str, body_radius: float = DEFAULT_BODY_RADIUS) -> Tuple[float, float, float]:
    """Return (x, y, z) mounting coordinate of the coxa pivot in body coordinates."""
    angle_deg = LEG_MOUNT_ANGLES_DEG.get(leg, 0.0)
    angle_rad = math.radians(angle_deg)
    x = body_radius * math.cos(angle_rad)
    y = body_radius * math.sin(angle_rad)
    z = 0.0
    return x, y, z

