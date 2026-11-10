"""
app/robotics/gait.py

Tripod Gait Generator for HEX-01 (Simulation Only).
Tripod A: Left Front (LF), Right Middle (RM), Left Rear (LR)
Tripod B: Right Front (RF), Left Middle (LM), Right Rear (RR)

Generates smooth cycloid swing foot trajectories and calculates 18 joint angle targets via IK.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple
from app.robotics.kinematics import HexapodKinematicsEngine
from app.robotics.robot_config import LEG_LABELS

TRIPOD_A = ["LF", "RM", "LR"]
TRIPOD_B = ["RF", "LM", "RR"]


class TripodGaitGenerator:
    def __init__(self, kinematics: HexapodKinematicsEngine):
        self.kinematics = kinematics
        self.step_length_m = 0.040     # 40 mm forward stride
        self.step_height_m = 0.025     # 25 mm foot lift clearance
        self.cycle_period_s = 1.2      # 1.2s per full step cycle
        self.phase = 0.0               # 0.0 to 1.0

        # Calculate neutral local stance position for each leg
        self.neutral_local_feet: Dict[str, Tuple[float, float, float]] = {}
        neutral_joints = self.kinematics.get_neutral_standing_pose_joint_targets()
        for leg, (c, f, t) in neutral_joints.items():
            self.neutral_local_feet[leg] = self.kinematics.solve_leg_fk(c, f, t)

    def update(self, dt: float, walk_velocity_m_s: float = 0.03) -> Dict[str, Tuple[float, float, float]]:
        """Advance the gait cycle phase by dt and return joint angles (coxa, femur, tibia) per leg."""
        if walk_velocity_m_s == 0.0:
            return self.kinematics.get_neutral_standing_pose_joint_targets()

        self.phase = (self.phase + (dt / self.cycle_period_s)) % 1.0

        joint_targets: Dict[str, Tuple[float, float, float]] = {}

        for leg in LEG_LABELS:
            is_tripod_a = leg in TRIPOD_A
            # Leg phase offset: Tripod B is 180 degrees (0.5) out of phase with Tripod A
            leg_phase = self.phase if is_tripod_a else (self.phase + 0.5) % 1.0

            base_x, base_y, base_z = self.neutral_local_feet[leg]

            if leg_phase < 0.5:
                # SWING PHASE: Foot lifts and moves forward
                progress = leg_phase / 0.5  # 0 to 1
                dx = -self.step_length_m / 2.0 + progress * self.step_length_m
                # Parabolic / sinusoidal lift
                dz = math.sin(progress * math.pi) * self.step_height_m
            else:
                # STANCE PHASE: Foot remains on ground, driving body forward
                progress = (leg_phase - 0.5) / 0.5  # 0 to 1
                dx = self.step_length_m / 2.0 - progress * self.step_length_m
                dz = 0.0

            target_foot = (base_x + dx, base_y, base_z + dz)
            ik_res = self.kinematics.solve_leg_ik(*target_foot)

            if ik_res is not None:
                joint_targets[leg] = ik_res
            else:
                # Fallback to neutral stance if close to boundary
                joint_targets[leg] = self.kinematics.get_neutral_standing_pose_joint_targets()[leg]

        return joint_targets

