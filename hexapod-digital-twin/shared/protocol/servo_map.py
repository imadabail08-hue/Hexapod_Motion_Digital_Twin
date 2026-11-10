"""
shared/protocol/servo_map.py

Servo ID enumeration, name mapping, and joint configuration for the
18-DOF hexapod robot (6 legs × 3 joints: coxa, femur, tibia).

Leg naming convention:
  LF = Left-Front   RF = Right-Front
  LM = Left-Middle  RM = Right-Middle
  LR = Left-Rear    RR = Right-Rear

Servo IDs are assigned sequentially:
  [LF_COXA=0, LF_FEMUR=1, LF_TIBIA=2,
   RF_COXA=3, RF_FEMUR=4, RF_TIBIA=5,
   LM_COXA=6, LM_FEMUR=7, LM_TIBIA=8,
   RM_COXA=9, RM_FEMUR=10, RM_TIBIA=11,
   LR_COXA=12, LR_FEMUR=13, LR_TIBIA=14,
   RR_COXA=15, RR_FEMUR=16, RR_TIBIA=17]
"""

from enum import IntEnum
from typing import Dict, Any


class ServoId(IntEnum):
    """18-DOF servo identifiers for a hexapod robot."""

    # Left-Front leg
    LF_COXA = 0
    LF_FEMUR = 1
    LF_TIBIA = 2

    # Right-Front leg
    RF_COXA = 3
    RF_FEMUR = 4
    RF_TIBIA = 5

    # Left-Middle leg
    LM_COXA = 6
    LM_FEMUR = 7
    LM_TIBIA = 8

    # Right-Middle leg
    RM_COXA = 9
    RM_FEMUR = 10
    RM_TIBIA = 11

    # Left-Rear leg
    LR_COXA = 12
    LR_FEMUR = 13
    LR_TIBIA = 14

    # Right-Rear leg
    RR_COXA = 15
    RR_FEMUR = 16
    RR_TIBIA = 17


# ---------------------------------------------------------------------------
# Human-readable name mapping  id → "LEG_SEGMENT"
# ---------------------------------------------------------------------------
SERVO_NAMES: Dict[int, str] = {
    ServoId.LF_COXA:  "LF_COXA",
    ServoId.LF_FEMUR: "LF_FEMUR",
    ServoId.LF_TIBIA: "LF_TIBIA",

    ServoId.RF_COXA:  "RF_COXA",
    ServoId.RF_FEMUR: "RF_FEMUR",
    ServoId.RF_TIBIA: "RF_TIBIA",

    ServoId.LM_COXA:  "LM_COXA",
    ServoId.LM_FEMUR: "LM_FEMUR",
    ServoId.LM_TIBIA: "LM_TIBIA",

    ServoId.RM_COXA:  "RM_COXA",
    ServoId.RM_FEMUR: "RM_FEMUR",
    ServoId.RM_TIBIA: "RM_TIBIA",

    ServoId.LR_COXA:  "LR_COXA",
    ServoId.LR_FEMUR: "LR_FEMUR",
    ServoId.LR_TIBIA: "LR_TIBIA",

    ServoId.RR_COXA:  "RR_COXA",
    ServoId.RR_FEMUR: "RR_FEMUR",
    ServoId.RR_TIBIA: "RR_TIBIA",
}


# ---------------------------------------------------------------------------
# Joint configuration
#
# Each entry describes the physical characteristics of a single DOF.
#
#   axis           : rotation axis in the robot's local coordinate system
#                    "X" = fore-aft tilt  |  "Y" = yaw  |  "Z" = lateral swing
#   direction      : +1 → positive command increases joint angle in the
#                    physically positive direction; -1 → inverted
#   neutral_offset : angular offset (deg) added to bring servo to the true
#                    mechanical neutral — set to 0.0 until measured
#   min_angle      : software-enforced minimum joint angle (deg)
#   max_angle      : software-enforced maximum joint angle (deg)
#   leg            : which leg this joint belongs to
#   segment        : "COXA", "FEMUR", or "TIBIA"
#
# Kinematic conventions:
#   Coxa  rotates around Z  — horizontal swing of the leg outward/inward
#   Femur rotates around X  — vertical lifting of the leg
#   Tibia rotates around X  — knee extension (direction=-1 → opposite sense)
#
# ---------------------------------------------------------------------------
JOINT_CONFIG: Dict[int, Dict[str, Any]] = {
    # ── Left-Front ──────────────────────────────────────────────────────────
    ServoId.LF_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LF", "segment": "COXA",
    },
    ServoId.LF_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LF", "segment": "FEMUR",
    },
    ServoId.LF_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LF", "segment": "TIBIA",
    },

    # ── Right-Front ──────────────────────────────────────────────────────────
    ServoId.RF_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RF", "segment": "COXA",
    },
    ServoId.RF_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RF", "segment": "FEMUR",
    },
    ServoId.RF_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RF", "segment": "TIBIA",
    },

    # ── Left-Middle ───────────────────────────────────────────────────────────
    ServoId.LM_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LM", "segment": "COXA",
    },
    ServoId.LM_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LM", "segment": "FEMUR",
    },
    ServoId.LM_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LM", "segment": "TIBIA",
    },

    # ── Right-Middle ──────────────────────────────────────────────────────────
    ServoId.RM_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RM", "segment": "COXA",
    },
    ServoId.RM_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RM", "segment": "FEMUR",
    },
    ServoId.RM_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RM", "segment": "TIBIA",
    },

    # ── Left-Rear ─────────────────────────────────────────────────────────────
    ServoId.LR_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LR", "segment": "COXA",
    },
    ServoId.LR_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LR", "segment": "FEMUR",
    },
    ServoId.LR_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "LR", "segment": "TIBIA",
    },

    # ── Right-Rear ────────────────────────────────────────────────────────────
    ServoId.RR_COXA: {
        "axis": "Z", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RR", "segment": "COXA",
    },
    ServoId.RR_FEMUR: {
        "axis": "X", "direction": +1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RR", "segment": "FEMUR",
    },
    ServoId.RR_TIBIA: {
        "axis": "X", "direction": -1, "neutral_offset": 0.0,
        "min_angle": -90.0, "max_angle": 90.0,
        "leg": "RR", "segment": "TIBIA",
    },
}


def get_leg_servo_ids(leg: str) -> list[int]:
    """Return the three servo IDs (coxa, femur, tibia) for a given leg label.

    Args:
        leg: One of "LF", "RF", "LM", "RM", "LR", "RR".

    Returns:
        List of three servo IDs in coxa→femur→tibia order.

    Raises:
        ValueError: If *leg* is not a recognised label.
    """
    ids = [sid for sid, cfg in JOINT_CONFIG.items() if cfg["leg"] == leg]
    if len(ids) != 3:
        raise ValueError(f"Unknown leg label: {leg!r}")
    # Sort by segment order: COXA < FEMUR < TIBIA
    order = {"COXA": 0, "FEMUR": 1, "TIBIA": 2}
    return sorted(ids, key=lambda sid: order[JOINT_CONFIG[sid]["segment"]])


# ---------------------------------------------------------------------------
# Convenience sets
# ---------------------------------------------------------------------------
ALL_SERVO_IDS: list[int] = list(range(18))
LEG_LABELS: list[str] = ["LF", "RF", "LM", "RM", "LR", "RR"]
