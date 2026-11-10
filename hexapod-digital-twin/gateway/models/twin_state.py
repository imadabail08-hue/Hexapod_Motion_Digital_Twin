"""
gateway/models/twin_state.py

Complete Pydantic v2 models representing every layer of the Digital Twin state.

State layers (never mixed):
  RAW_SENSOR_STATE    — directly from ESP32 JSON
  FILTERED_STATE      — computed pitch/roll/yaw after complementary filter
  CONTROL_STATE       — operating mode, authority, servo commands
  PHYSICAL_STATE      — actual hardware servo angle from ESP32
  SIMULATED_STATE     — from Webots (joint positions, orientation, foot contacts)
  DIGITAL_TWIN_STATE  — authoritative broadcast merged view
"""

from __future__ import annotations

import json
import math
import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _sanitize_float(v: float) -> float:
    """Return 0.0 if *v* is NaN or infinite, otherwise return *v* unchanged."""
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return v


# ---------------------------------------------------------------------------
# RAW_SENSOR_STATE
# ---------------------------------------------------------------------------

class ImuRaw(BaseModel):
    """Raw 6-axis IMU reading (accelerometer + gyroscope).

    Units: accelerometer in m/s², gyroscope in deg/s.
    Values that are NaN or Infinite are clamped to 0.0 at validation time.
    """

    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0

    @field_validator("ax", "ay", "az", "gx", "gy", "gz", mode="before")
    @classmethod
    def sanitize(cls, v: object) -> float:
        """Clamp NaN / Inf to 0.0."""
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return _sanitize_float(f)


# ---------------------------------------------------------------------------
# FILTERED_STATE
# ---------------------------------------------------------------------------

class ImuData(BaseModel):
    """Paired raw and complementary-filtered IMU data."""

    raw: ImuRaw = Field(default_factory=ImuRaw)
    filtered: ImuRaw = Field(default_factory=ImuRaw)


class Orientation(BaseModel):
    """Robot body orientation in Euler angles (degrees).

    Attributes:
        pitch:        Forward/backward tilt (deg).
        roll:         Side tilt (deg).
        yaw:          Heading (deg, relative unless yawAbsolute is True).
        yawAbsolute:  True when yaw is fused with an absolute heading source.
        pitchZero:    Pitch calibration offset (deg) subtracted at display time.
        rollZero:     Roll calibration offset (deg) subtracted at display time.
    """

    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    yawAbsolute: bool = False
    pitchZero: float = 0.0
    rollZero: float = 0.0

    @field_validator("pitch", "roll", "yaw", "pitchZero", "rollZero", mode="before")
    @classmethod
    def sanitize(cls, v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return _sanitize_float(f)


# ---------------------------------------------------------------------------
# PHYSICAL_STATE
# ---------------------------------------------------------------------------

class PhysicalServo(BaseModel):
    """State of a single physical servo as reported by the ESP32.

    Attributes:
        id:      Servo channel index (0–17).
        angle:   Current measured angle (PWM units, 50–130 typical).
        command: Last commanded angle sent to the servo.
        min:     Software-enforced minimum (PWM units).
        max:     Software-enforced maximum (PWM units).
    """

    id: int = 1
    angle: int = 90
    command: int = 90
    min: int = 50
    max: int = 130


# ---------------------------------------------------------------------------
# SIMULATED_STATE sub-models
# ---------------------------------------------------------------------------

class FootPosition(BaseModel):
    """3-D foot position in the robot body frame (metres).

    Attributes:
        leg: Leg label — one of "LF", "RF", "LM", "RM", "LR", "RR".
        x:   Forward component.
        y:   Lateral component (positive = left).
        z:   Vertical component (positive = up).
    """

    leg: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @field_validator("x", "y", "z", mode="before")
    @classmethod
    def sanitize(cls, v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return _sanitize_float(f)


# ---------------------------------------------------------------------------
# CONTROL_STATE
# ---------------------------------------------------------------------------

class ConnectionStatus(BaseModel):
    """Live connectivity status for all subsystems.

    Attributes:
        esp32:       True when ESP32 WebSocket session is active.
        webots:      True when Webots TCP bridge is connected.
        clientCount: Number of currently connected visualiser clients.
    """

    esp32: bool = False
    webots: bool = False
    clientCount: int = 0


# ---------------------------------------------------------------------------
# DIGITAL_TWIN_STATE — health metrics
# ---------------------------------------------------------------------------

class TwinHealth(BaseModel):
    """Quality-of-service metrics for the digital twin.

    Attributes:
        syncStatus:            "SYNC_GOOD" | "SYNC_DEGRADED" | "SYNC_LOST" | "UNKNOWN"
        packetAgeMs:           Age of the most recent ESP32 packet (ms).
        latencyMs:             Round-trip latency estimate (ms).
        telemetryHz:           Measured incoming telemetry rate (Hz).
        packetLoss:            Fraction of missed packets (0.0–1.0).
        orientationErrorPitch: Δ pitch between physical and simulated (deg).
        orientationErrorRoll:  Δ roll between physical and simulated (deg).
        maxServoError:         Maximum servo position discrepancy across all joints (deg).
        simulationRTF:         Webots real-time factor (1.0 = real-time).
    """

    syncStatus: str = "UNKNOWN"
    packetAgeMs: float = 0.0
    latencyMs: float = 0.0
    telemetryHz: float = 0.0
    packetLoss: float = 0.0
    orientationErrorPitch: float = 0.0
    orientationErrorRoll: float = 0.0
    maxServoError: float = 0.0
    simulationRTF: float = 0.0

    @field_validator(
        "packetAgeMs", "latencyMs", "telemetryHz", "packetLoss",
        "orientationErrorPitch", "orientationErrorRoll", "maxServoError",
        "simulationRTF",
        mode="before",
    )
    @classmethod
    def sanitize(cls, v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return _sanitize_float(f)


# ---------------------------------------------------------------------------
# DIGITAL_TWIN_STATE — authoritative top-level state
# ---------------------------------------------------------------------------

def _default_foot_positions() -> list[FootPosition]:
    """Return zeroed foot positions for all six legs."""
    return [FootPosition(leg=leg) for leg in ("LF", "RF", "LM", "RM", "LR", "RR")]


class DigitalTwinState(BaseModel):
    """Authoritative merged state broadcast to all connected clients.

    This model is the single source of truth consumed by Three.js, Ursina,
    Pygame, and any other visualiser.  It is populated by TwinStateManager
    and serialised to JSON for WebSocket broadcast.

    Attributes:
        timestamp:       Unix epoch milliseconds when this snapshot was created.
        sequence:        Monotonically increasing packet counter.
        mode:            Current operating mode string.
        emergencyStop:   True when the safety system has halted all motion.
        stabilization:   True when active body stabilization is engaged.
        connection:      Live connectivity flags for all subsystems.
        imu:             Raw + filtered IMU data from the ESP32 (or simulated).
        orientation:     Body orientation Euler angles (deg).
        physicalServo:   State of the single monitored physical servo.
        virtualServos:   Commanded angles for all 18 virtual joints (deg).
        simulatedServos: Joint angles reported by Webots (deg).
        servoErrors:     Element-wise absolute error virtual − simulated (deg).
        footPositions:   Foot positions from forward kinematics or Webots.
        twinHealth:      QoS metrics.
    """

    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    sequence: int = 0
    mode: str = "SIMULATION"
    emergencyStop: bool = False
    stabilization: bool = True

    connection: ConnectionStatus = Field(default_factory=ConnectionStatus)
    imu: ImuData = Field(default_factory=ImuData)
    orientation: Orientation = Field(default_factory=Orientation)
    physicalServo: PhysicalServo = Field(default_factory=PhysicalServo)

    virtualServos: list[float] = Field(default_factory=lambda: [90.0] * 18)
    simulatedServos: list[float] = Field(default_factory=lambda: [90.0] * 18)
    servoErrors: list[float] = Field(default_factory=lambda: [0.0] * 18)
    footPositions: list[FootPosition] = Field(default_factory=_default_foot_positions)

    twinHealth: TwinHealth = Field(default_factory=TwinHealth)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_broadcast_json(self) -> str:
        """Serialise the state to a compact JSON string for WebSocket broadcast.

        Returns:
            JSON string with no extra whitespace.
        """
        return self.model_dump_json()

    @classmethod
    def from_broadcast_json(cls, json_str: str) -> Optional["DigitalTwinState"]:
        """Deserialise a broadcast JSON string back into a DigitalTwinState.

        Args:
            json_str: JSON string produced by :meth:`to_broadcast_json`.

        Returns:
            Parsed instance, or *None* on any parse / validation error.
        """
        try:
            data = json.loads(json_str)
            return cls.model_validate(data)
        except Exception:  # noqa: BLE001
            return None
