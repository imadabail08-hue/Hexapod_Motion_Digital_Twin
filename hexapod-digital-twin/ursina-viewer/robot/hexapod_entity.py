"""
Hexapod Entity — Ursina 3D representation of the hexapod robot.

Hierarchy
---------
body (Entity)
└── [for each of 6 legs]
    └── coxa_pivot (Entity)  — rotates on Z/Y axis (swing)
        └── coxa_link (Entity)
            └── femur_pivot (Entity) — rotates on X axis (lift)
                └── femur_link (Entity)
                    └── tibia_pivot (Entity) — rotates on X axis (reach)
                        └── tibia_link (Entity)
                            └── foot (Entity) — sphere, changes colour on contact

Joint angle convention
----------------------
  virtualServos list:  18 values in degrees, range [0, 180], 90 = neutral.
  For display: convert to ±90° centred at 0.

Left legs (indices 0,1,2 = LF,LM,LR): coxa swings in +Z direction
Right legs (indices 3,4,5 = RF,RM,RR): coxa swings in -Z direction
"""

from ursina import Entity, Text, Vec3, color
import math

# ---------------------------------------------------------------------------
# Geometric constants  [PLACEHOLDER — tune from physical robot measurements]
# ---------------------------------------------------------------------------

# Body attachment offsets from body centre (Ursina X,Y,Z)
# Left side:  X negative  (Ursina X = body right, so left = negative)
# NOTE: Ursina coordinate: X=right, Y=up, Z=toward viewer
LEG_ATTACHMENTS = [
    # (  X,     Y,     Z  )   leg name
    (-0.09,  0.0,  0.06),   # LF  0
    (-0.09,  0.0,  0.00),   # LM  1
    (-0.09,  0.0, -0.06),   # LR  2
    ( 0.09,  0.0,  0.06),   # RF  3
    ( 0.09,  0.0,  0.00),   # RM  4
    ( 0.09,  0.0, -0.06),   # RR  5
]

LEG_NAMES     = ["LF", "LM", "LR", "RF", "RM", "RR"]
FOOT_NAMES    = ["lf_foot", "lm_foot", "lr_foot", "rf_foot", "rm_foot", "rr_foot"]

COXA_LEN      = 0.040   # metres
FEMUR_LEN     = 0.060
TIBIA_LEN     = 0.070

_LINK_W       = 0.010   # cross-section width/height of link boxes

# Colours (HSL-ish via Ursina color.color(h,s,v))
_C_BODY       = color.color(0.60, 0.85, 0.15, 1)   # near-black blue
_C_COXA       = color.color(0.55, 0.70, 0.45, 1)   # dark steel
_C_FEMUR      = color.color(0.55, 0.65, 0.40, 1)
_C_TIBIA      = color.color(0.55, 0.60, 0.35, 1)
_C_FOOT_OFF   = color.yellow
_C_FOOT_ON    = color.lime                          # contact = green


class HexapodEntity:
    """
    Lightweight Ursina entity hierarchy for hexapod visualisation.

    Parameters
    ----------
    None — constructed with default body centre at world origin.
    """

    def __init__(self):
        # ----------------------------------------------------------------
        # Body
        # ----------------------------------------------------------------
        self.body = Entity(
            model="cube",
            scale=(0.18, 0.040, 0.12),
            color=_C_BODY,
            collider=None,
        )

        # Body top panel (slightly lighter)
        Entity(
            parent=self.body,
            model="cube",
            scale=(0.95, 0.1, 0.90),
            position=(0, 0.55, 0),
            color=color.color(0.60, 0.80, 0.20, 1),
        )

        # Body centre indicator dot
        Entity(
            parent=self.body,
            model="sphere",
            scale=0.12,
            position=(0, 0.7, 0),
            color=color.color(0.57, 1, 1, 1),
        )

        # ----------------------------------------------------------------
        # Legs — (coxa_pivot, coxa_link, femur_pivot, femur_link,
        #          tibia_pivot, tibia_link, foot)
        # ----------------------------------------------------------------
        self.leg_joints = []   # list of tuples (coxa_p, femur_p, tibia_p, foot_e)
        self._foot_entities: dict[str, Entity] = {}

        for i, (ax, ay, az) in enumerate(LEG_ATTACHMENTS):
            is_right = (i >= 3)
            side     = -1 if is_right else 1   # direction of coxa extension

            # -- Coxa pivot (attached to body) --------------------------
            coxa_pivot = Entity(
                parent=self.body,
                position=(
                    ax / 0.18,    # normalise into body local space
                    ay / 0.040,
                    az / 0.12,
                ),
                color=color.clear,
            )

            # Coxa visual link (extends outward from pivot)
            coxa_link = Entity(
                parent=coxa_pivot,
                model="cube",
                scale=(COXA_LEN * 5.5, _LINK_W * 0.5, _LINK_W * 0.5),
                position=(side * COXA_LEN * 2.75, 0, 0),
                color=_C_COXA,
            )

            # Label
            Text(
                text=LEG_NAMES[i],
                parent=coxa_pivot,
                scale=4.0,
                position=(0, 0.12, 0),
                color=color.cyan,
                billboard=True,
            )

            # -- Femur pivot --------------------------------------------
            femur_pivot = Entity(
                parent=coxa_pivot,
                position=(side * COXA_LEN * 5.5, 0, 0),
                color=color.clear,
            )

            femur_link = Entity(
                parent=femur_pivot,
                model="cube",
                scale=(FEMUR_LEN * 5.5, _LINK_W * 0.45, _LINK_W * 0.45),
                position=(side * FEMUR_LEN * 2.75, 0, 0),
                color=_C_FEMUR,
            )

            # -- Tibia pivot --------------------------------------------
            tibia_pivot = Entity(
                parent=femur_pivot,
                position=(side * FEMUR_LEN * 5.5, 0, 0),
                color=color.clear,
            )

            tibia_link = Entity(
                parent=tibia_pivot,
                model="cube",
                scale=(TIBIA_LEN * 5.5, _LINK_W * 0.40, _LINK_W * 0.40),
                position=(side * TIBIA_LEN * 2.75, 0, 0),
                color=_C_TIBIA,
            )

            # -- Foot sphere -------------------------------------------
            foot_e = Entity(
                parent=tibia_pivot,
                model="sphere",
                scale=0.8,
                position=(side * TIBIA_LEN * 5.5, 0, 0),
                color=_C_FOOT_OFF,
            )

            self.leg_joints.append((coxa_pivot, femur_pivot, tibia_pivot, foot_e))
            self._foot_entities[FOOT_NAMES[i]] = foot_e

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_servo_angles(self, angles: list):
        """
        Apply 18 servo angles (degrees, 0–180 range) to the leg hierarchy.

        Parameters
        ----------
        angles : list[float]
            18 values ordered as:
            [lf_coxa, lf_femur, lf_tibia,
             lm_coxa, lm_femur, lm_tibia,
             lr_coxa, lr_femur, lr_tibia,
             rf_coxa, rf_femur, rf_tibia,
             rm_coxa, rm_femur, rm_tibia,
             rr_coxa, rr_femur, rr_tibia]
        """
        if len(angles) < 18:
            return

        for i, (coxa_p, femur_p, tibia_p, _foot) in enumerate(self.leg_joints):
            base = i * 3
            coxa_deg  = float(angles[base])     - 90.0   # convert to ±90
            femur_deg = float(angles[base + 1]) - 90.0
            tibia_deg = float(angles[base + 2]) - 90.0

            is_right = (i >= 3)

            # Coxa swings the leg forward/back (rotation around Y axis)
            coxa_p.rotation_y  = coxa_deg * (-1 if is_right else 1)

            # Femur lifts the leg (rotation around Z axis in local space)
            femur_p.rotation_z = femur_deg * (-1 if is_right else 1)

            # Tibia reaches (rotation around Z axis, typically inverted)
            tibia_p.rotation_z = -tibia_deg * (-1 if is_right else 1)

    def update_foot_contacts(self, contacts: dict):
        """
        Update foot sphere colours based on contact dict.

        Parameters
        ----------
        contacts : dict[str, bool]
            e.g. {"lf_foot": True, "lm_foot": False, ...}
        """
        for foot_name, foot_entity in self._foot_entities.items():
            in_contact = contacts.get(foot_name, False)
            foot_entity.color = _C_FOOT_ON if in_contact else _C_FOOT_OFF
