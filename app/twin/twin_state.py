"""
app/twin/twin_state.py

Authoritative Unified Digital Twin State model for HEX-01.
Merges Physical Hardware State, Multi-Body Simulation State,
Command Targets, and Twin Health Diagnostics.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple
from app.twin.physical_state import PhysicalHardwareState
from app.twin.simulation_state import SimulationState
from app.twin.health import TwinHealthReport
from app.robotics.robot_config import (
    JOINT_NAMES,
    STAND_COXA_DEG,
    STAND_FEMUR_DEG,
    STAND_TIBIA_DEG,
)


class OperatingMode(str, Enum):
    LIVE_HARDWARE = "LIVE_HARDWARE"
    SIMULATION    = "SIMULATION"
    MIRROR_18     = "MIRROR_18"
    MANUAL        = "MANUAL"
    REPLAY        = "REPLAY"


@dataclass
class DigitalTwinState:
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    sequence_id: int = 0
    mode: OperatingMode = OperatingMode.SIMULATION

    # Safety system
    emergency_stop: bool = False
    stabilization_active: bool = True
    hardware_command_gate_enabled: bool = False

    # Component states
    physical: PhysicalHardwareState = field(default_factory=PhysicalHardwareState)
    simulation: SimulationState = field(default_factory=SimulationState)
    health: TwinHealthReport = field(default_factory=TwinHealthReport)

    # 18 Virtual Commanded Joint Targets (degrees) — initialized to POSE_NEUTRAL_STAND
    target_joint_angles: Dict[str, float] = field(default_factory=lambda: {
        name: (
            STAND_COXA_DEG if "coxa" in name
            else STAND_FEMUR_DEG if "femur" in name
            else STAND_TIBIA_DEG
        )
        for name in JOINT_NAMES
    })

    # Body-frame foot positions (x, y, z meters)
    foot_positions_body_frame: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)

