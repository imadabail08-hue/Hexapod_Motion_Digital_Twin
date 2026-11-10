"""
app/twin/simulation_state.py

Represents the multi-body physics simulation state received from Webots.
Decoupled from physical hardware and visual rendering.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from app.robotics.robot_config import JOINT_NAMES, FOOT_SENSOR_NAMES, STAND_COXA_DEG, STAND_FEMUR_DEG, STAND_TIBIA_DEG


@dataclass
class SimulationState:
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    webots_running: bool = False
    simulation_time_s: float = 0.0
    real_time_factor: float = 1.0  # 1.0 = real-time

    # Simulated orientation from Webots InertialUnit (degrees)
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    yaw_deg: float = 0.0

    # 18 Joint measured angles from Webots PositionSensors (degrees)
    # Default initialized to POSE_NEUTRAL_STAND
    simulated_joint_angles: Dict[str, float] = field(default_factory=lambda: {
        name: (
            STAND_COXA_DEG if "coxa" in name
            else STAND_FEMUR_DEG if "femur" in name
            else STAND_TIBIA_DEG
        )
        for name in JOINT_NAMES
    })

    # Foot contact states from Webots TouchSensors (True = contact with floor)
    foot_contacts: Dict[str, bool] = field(default_factory=lambda: {
        name: True for name in FOOT_SENSOR_NAMES
    })

    # Foot positions calculated from physics engine (x, y, z meters in body frame)
    foot_positions_m: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)

