"""
app/robotics/kinematics.py

Comprehensive Kinematics Engine for the HEX-01 Hexapod.
Manages Forward and Inverse Kinematics for all 6 articulated legs.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from app.robotics.robot_config import (
    HexapodDimensions,
    LEG_LABELS,
    STAND_COXA_DEG,
    STAND_FEMUR_DEG,
    STAND_TIBIA_DEG,
    STAND_CLEARANCE_HEIGHT_M,
)
from app.robotics.forward_kinematics import forward_kinematics_3dof
from app.robotics.inverse_kinematics import inverse_kinematics_3dof
from app.robotics.coordinate_frames import leg_local_to_body, body_to_leg_local


class HexapodKinematicsEngine:
    def __init__(self, dims: Optional[HexapodDimensions] = None):
        self.dims = dims or HexapodDimensions()

    def solve_leg_fk(self, coxa_deg: float, femur_deg: float, tibia_deg: float) -> Tuple[float, float, float]:
        """Compute local foot position (x, y, z) in meters relative to coxa pivot."""
        return forward_kinematics_3dof(
            coxa_deg, femur_deg, tibia_deg,
            self.dims.coxa_len, self.dims.femur_len, self.dims.tibia_len,
        )

    def solve_leg_ik(self, target_x: float, target_y: float, target_z: float) -> Optional[Tuple[float, float, float]]:
        """Compute local joint angles (coxa, femur, tibia) from local foot position."""
        return inverse_kinematics_3dof(
            target_x, target_y, target_z,
            self.dims.coxa_len, self.dims.femur_len, self.dims.tibia_len,
        )

    def get_neutral_standing_pose_joint_targets(self) -> Dict[str, Tuple[float, float, float]]:
        """Return the POSE_NEUTRAL_STAND joint angles for all 6 legs."""
        return {
            leg: (STAND_COXA_DEG, STAND_FEMUR_DEG, STAND_TIBIA_DEG)
            for leg in LEG_LABELS
        }

    def compute_all_foot_positions_body_frame(
        self, joint_angles: Dict[str, Tuple[float, float, float]]
    ) -> Dict[str, Tuple[float, float, float]]:
        """Given joint angles per leg, compute each foot's 3D position in Robot Body frame."""
        foot_positions = {}
        for leg, (c, f, t) in joint_angles.items():
            lx, ly, lz = self.solve_leg_fk(c, f, t)
            bx, by, bz = leg_local_to_body(leg, lx, ly, lz)
            foot_positions[leg] = (round(bx, 4), round(by, 4), round(bz, 4))
        return foot_positions

