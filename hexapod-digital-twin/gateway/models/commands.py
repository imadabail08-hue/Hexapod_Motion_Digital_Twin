"""
gateway/models/commands.py

Command envelope model for instructions sent from visualiser clients
(Three.js, Ursina, Pygame) to the gateway over the client WebSocket
on port 8080.

Commands can also be submitted via the HTTP POST /command endpoint.

Expected JSON envelope:
{
    "type": "command",
    "command": "SET_SERVO",
    "params": {"id": 3, "angle": 75}
}
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class CommandType(str, Enum):
    """All supported gateway command types.

    Commands are grouped by function:

    **IMU calibration**
      CALIBRATE_IMU       — run zero-bias calibration routine
      RESET_YAW           — set current heading as yaw = 0

    **Servo control**
      CENTER_SERVO        — move physical servo to its neutral position
      SET_SERVO           — set a specific servo to a specified angle

    **Stabilization**
      ENABLE_STABILIZATION  — engage active body levelling
      DISABLE_STABILIZATION — disengage active body levelling

    **Operating mode**
      ENABLE_MIRROR_18    — map the single monitored servo across all 18 joints
      SET_MODE            — switch operating mode (see OperatingMode)

    **Safety**
      EMERGENCY_STOP      — immediately halt all motion
      RESET_EMERGENCY_STOP — clear the emergency stop latch

    **Recording / replay**
      START_RECORDING     — begin telemetry capture
      STOP_RECORDING      — end telemetry capture
      REPLAY_PLAY         — start or resume recorded playback
      REPLAY_PAUSE        — pause recorded playback
      REPLAY_RESTART      — restart playback from the beginning
      REPLAY_SPEED        — set playback speed multiplier (0.5, 1.0, 2.0)
    """

    # IMU calibration
    CALIBRATE_IMU = "CALIBRATE_IMU"
    RESET_YAW = "RESET_YAW"

    # Servo control
    CENTER_SERVO = "CENTER_SERVO"
    SET_SERVO = "SET_SERVO"

    # Stabilization
    ENABLE_STABILIZATION = "ENABLE_STABILIZATION"
    DISABLE_STABILIZATION = "DISABLE_STABILIZATION"

    # Mode / mirror
    ENABLE_MIRROR_18 = "ENABLE_MIRROR_18"
    SET_MODE = "SET_MODE"

    # Safety
    EMERGENCY_STOP = "EMERGENCY_STOP"
    RESET_EMERGENCY_STOP = "RESET_EMERGENCY_STOP"

    # Recording / replay
    START_RECORDING = "START_RECORDING"
    STOP_RECORDING = "STOP_RECORDING"
    REPLAY_PLAY = "REPLAY_PLAY"
    REPLAY_PAUSE = "REPLAY_PAUSE"
    REPLAY_RESTART = "REPLAY_RESTART"
    REPLAY_SPEED = "REPLAY_SPEED"


# Mapping from CommandType to required parameter keys
_REQUIRED_PARAMS: dict[CommandType, set[str]] = {
    CommandType.SET_SERVO:   {"id", "angle"},
    CommandType.SET_MODE:    {"mode"},
    CommandType.REPLAY_SPEED: {"speed"},
}


class CommandEnvelope(BaseModel):
    """A command message from a client to the gateway.

    Attributes:
        type:    Fixed discriminator tag — must equal "command".
        command: One of the :class:`CommandType` values.
        params:  Optional key-value arguments for the command.
    """

    type: str = "command"
    command: CommandType
    params: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, json_str: str) -> Optional["CommandEnvelope"]:
        """Parse a raw JSON string into a CommandEnvelope.

        Args:
            json_str: Raw JSON text from a WebSocket or HTTP request body.

        Returns:
            Parsed envelope, or *None* on any parse/validation failure.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.debug("Command JSON parse error: %s", exc)
            return None
        try:
            return cls.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Command validation error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _check_type_tag(self) -> "CommandEnvelope":
        """Enforce the 'command' type discriminator."""
        if self.type != "command":
            raise ValueError(f"Expected type='command', got {self.type!r}")
        return self

    def validate(self) -> bool:  # noqa: A003
        """Check that all required params for this command are present.

        Returns:
            True if the command is internally consistent and has all
            mandatory parameters; False otherwise.
        """
        required = _REQUIRED_PARAMS.get(self.command, set())
        missing = required - set(self.params.keys())
        if missing:
            logger.warning(
                "Command %s missing required params: %s",
                self.command.value,
                missing,
            )
            return False
        return True
