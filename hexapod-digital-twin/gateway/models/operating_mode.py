"""
gateway/models/operating_mode.py

Operating mode enumeration and the finite-state machine that governs
legal mode transitions for the Digital Twin Gateway.

Mode descriptions:
  LIVE_HARDWARE — ESP32 is connected; physical servos are the authority.
  SIMULATION    — Webots drives the model; no physical hardware required.
  MIRROR_18     — Single monitored servo is mirrored across all 18 joints.
  MANUAL        — Operator sends explicit SET_SERVO commands.
  REPLAY        — Recorded telemetry is played back at configurable speed.
"""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class OperatingMode(str, Enum):
    """Legal operating modes for the gateway.

    The str mixin lets these values be used directly as JSON strings.
    """

    LIVE_HARDWARE = "LIVE_HARDWARE"
    SIMULATION = "SIMULATION"
    MIRROR_18 = "MIRROR_18"
    MANUAL = "MANUAL"
    REPLAY = "REPLAY"


# Legal (source, destination) transitions.
# Any pair NOT listed here is forbidden.
_ALLOWED_TRANSITIONS: set[tuple[OperatingMode, OperatingMode]] = {
    # From SIMULATION (default/safe starting mode)
    (OperatingMode.SIMULATION,    OperatingMode.LIVE_HARDWARE),
    (OperatingMode.SIMULATION,    OperatingMode.MIRROR_18),
    (OperatingMode.SIMULATION,    OperatingMode.MANUAL),
    (OperatingMode.SIMULATION,    OperatingMode.REPLAY),

    # From LIVE_HARDWARE
    (OperatingMode.LIVE_HARDWARE, OperatingMode.SIMULATION),
    (OperatingMode.LIVE_HARDWARE, OperatingMode.MIRROR_18),
    (OperatingMode.LIVE_HARDWARE, OperatingMode.MANUAL),
    (OperatingMode.LIVE_HARDWARE, OperatingMode.REPLAY),

    # From MIRROR_18
    (OperatingMode.MIRROR_18,     OperatingMode.SIMULATION),
    (OperatingMode.MIRROR_18,     OperatingMode.LIVE_HARDWARE),
    (OperatingMode.MIRROR_18,     OperatingMode.MANUAL),
    (OperatingMode.MIRROR_18,     OperatingMode.REPLAY),

    # From MANUAL
    (OperatingMode.MANUAL,        OperatingMode.SIMULATION),
    (OperatingMode.MANUAL,        OperatingMode.LIVE_HARDWARE),
    (OperatingMode.MANUAL,        OperatingMode.MIRROR_18),
    (OperatingMode.MANUAL,        OperatingMode.REPLAY),

    # From REPLAY
    (OperatingMode.REPLAY,        OperatingMode.SIMULATION),
    (OperatingMode.REPLAY,        OperatingMode.LIVE_HARDWARE),
    (OperatingMode.REPLAY,        OperatingMode.MIRROR_18),
    (OperatingMode.REPLAY,        OperatingMode.MANUAL),
}

# Modes that require an active ESP32 connection to enter
_REQUIRES_ESP32: set[OperatingMode] = {
    OperatingMode.LIVE_HARDWARE,
    OperatingMode.MIRROR_18,
}

# Maps mode → which subsystem holds servo authority
_AUTHORITY_MAP: dict[OperatingMode, str] = {
    OperatingMode.LIVE_HARDWARE: "ESP32",
    OperatingMode.SIMULATION:    "WEBOTS",
    OperatingMode.MIRROR_18:     "ESP32",
    OperatingMode.MANUAL:        "MANUAL",
    OperatingMode.REPLAY:        "REPLAY",
}


class ModeStateMachine:
    """Governs legal operating-mode transitions for the gateway.

    Attributes:
        current:          The currently active :class:`OperatingMode`.
        hardware_enabled: Physical servo enable gate.  Only relevant in
                          MANUAL mode — when False, SET_SERVO commands are
                          processed virtually but not forwarded to the ESP32.
    """

    def __init__(self, initial: OperatingMode = OperatingMode.SIMULATION) -> None:
        self.current: OperatingMode = initial
        self.hardware_enabled: bool = False

    # ------------------------------------------------------------------
    # Transition
    # ------------------------------------------------------------------

    def transition(self, new_mode: OperatingMode, esp32_connected: bool) -> bool:
        """Attempt to transition to *new_mode*.

        Args:
            new_mode:       The desired target mode.
            esp32_connected: Whether an ESP32 WebSocket session is active.
                             Required for LIVE_HARDWARE and MIRROR_18 modes.

        Returns:
            True if the transition was accepted and applied; False if it was
            rejected (invalid transition or missing prerequisite).
        """
        if new_mode == self.current:
            logger.debug("Mode unchanged: %s", new_mode.value)
            return True

        if (self.current, new_mode) not in _ALLOWED_TRANSITIONS:
            logger.warning(
                "Illegal mode transition %s → %s rejected",
                self.current.value,
                new_mode.value,
            )
            return False

        if new_mode in _REQUIRES_ESP32 and not esp32_connected:
            logger.warning(
                "Mode %s requires ESP32 connection — transition rejected",
                new_mode.value,
            )
            return False

        logger.info(
            "Mode transition: %s → %s", self.current.value, new_mode.value
        )
        self.current = new_mode

        # Reset hardware enable when leaving MANUAL mode
        if new_mode != OperatingMode.MANUAL:
            self.hardware_enabled = False

        return True

    # ------------------------------------------------------------------
    # Authority
    # ------------------------------------------------------------------

    def get_servo_authority(self) -> str:
        """Return a string indicating which subsystem controls the servos.

        Returns:
            One of ``"ESP32"``, ``"WEBOTS"``, ``"MANUAL"``, or ``"REPLAY"``.
        """
        return _AUTHORITY_MAP[self.current]

    # ------------------------------------------------------------------
    # Convenience predicates
    # ------------------------------------------------------------------

    def is_hardware_mode(self) -> bool:
        """Return True when real hardware is active (physical servo output enabled)."""
        return self.current in (
            OperatingMode.LIVE_HARDWARE,
            OperatingMode.MIRROR_18,
        )

    def __repr__(self) -> str:
        return (
            f"ModeStateMachine(current={self.current.value!r}, "
            f"hardware_enabled={self.hardware_enabled})"
        )
