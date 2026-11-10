"""
gateway/models/telemetry.py

Pydantic v2 model for the telemetry packet sent by the ESP32 firmware
over the WebSocket connection on port 8765.

Expected JSON structure from ESP32:
{
    "type": "telemetry",
    "timestamp": 1234567890,
    "imu": {
        "ax": 0.01, "ay": -0.02, "az": 9.81,
        "gx": 0.1,  "gy": -0.3,  "gz": 0.05
    },
    "orientation": {
        "pitch": 1.2, "roll": -0.5, "yaw": 45.0
    },
    "servo": {
        "id": 1, "angle": 90, "command": 90, "min": 50, "max": 130
    },
    "mode": "LIVE_HARDWARE"
}
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

# Sanity-check limits applied during validation
_IMU_ACCEL_MAX: float = 40.0   # m/s² — ~4 g, well above any reasonable motion
_IMU_GYRO_MAX: float = 2000.0  # deg/s — typical maximum for MEMS gyros
_ANGLE_MAX: float = 360.0      # deg  — orientation wrap limit


class ESP32TelemetryPacket(BaseModel):
    """A single telemetry packet received from the ESP32 firmware.

    Attributes:
        type:        Packet type tag — must be "telemetry".
        timestamp:   ESP32 millis() timestamp (milliseconds since boot).
        imu:         Raw IMU fields (ax/ay/az in m/s², gx/gy/gz in deg/s).
        orientation: Euler angles computed on the ESP32 (deg).
        servo:       State of the single monitored physical servo.
        mode:        Operating mode string reported by the ESP32.
    """

    type: str = "telemetry"
    timestamp: int = 0
    imu: dict[str, Any] = Field(default_factory=dict)
    orientation: dict[str, Any] = Field(default_factory=dict)
    servo: dict[str, Any] = Field(default_factory=dict)
    mode: str = "LIVE_HARDWARE"

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _normalise_fields(self) -> "ESP32TelemetryPacket":
        """Ensure numeric sub-fields exist and are finite."""
        # IMU defaults
        for key in ("ax", "ay", "az", "gx", "gy", "gz"):
            v = self.imu.get(key, 0.0)
            self.imu[key] = _safe_float(v, 0.0)

        # Orientation defaults
        for key in ("pitch", "roll", "yaw"):
            v = self.orientation.get(key, 0.0)
            self.orientation[key] = _safe_float(v, 0.0)

        # Servo defaults
        servo_defaults: dict[str, int] = {
            "id": 1, "angle": 90, "command": 90, "min": 50, "max": 130
        }
        for key, default in servo_defaults.items():
            v = self.servo.get(key, default)
            try:
                self.servo[key] = int(v)
            except (TypeError, ValueError):
                self.servo[key] = default

        return self

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, json_str: str) -> Optional["ESP32TelemetryPacket"]:
        """Parse a raw JSON string from the ESP32 WebSocket stream.

        Args:
            json_str: Raw JSON text received from the WebSocket.

        Returns:
            Parsed packet, or *None* if the string is not valid JSON or
            fails Pydantic validation.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.debug("ESP32 JSON parse error: %s — raw: %.120s", exc, json_str)
            return None

        try:
            return cls.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            logger.debug("ESP32 telemetry validation error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validate_ranges(self) -> bool:
        """Perform physical-range sanity checks on all numeric fields.

        Checks:
          * All IMU accelerometer values within ±``_IMU_ACCEL_MAX`` m/s².
          * All IMU gyroscope values within ±``_IMU_GYRO_MAX`` deg/s.
          * All orientation values within ±``_ANGLE_MAX`` degrees.
          * No NaN or Inf values anywhere.

        Returns:
            True if every value is within expected physical limits.
        """
        # Accelerometer
        for key in ("ax", "ay", "az"):
            v = self.imu.get(key, 0.0)
            if not _is_finite_and_in_range(v, -_IMU_ACCEL_MAX, _IMU_ACCEL_MAX):
                logger.warning("IMU accel out of range: %s=%s", key, v)
                return False

        # Gyroscope
        for key in ("gx", "gy", "gz"):
            v = self.imu.get(key, 0.0)
            if not _is_finite_and_in_range(v, -_IMU_GYRO_MAX, _IMU_GYRO_MAX):
                logger.warning("IMU gyro out of range: %s=%s", key, v)
                return False

        # Orientation
        for key in ("pitch", "roll", "yaw"):
            v = self.orientation.get(key, 0.0)
            if not _is_finite_and_in_range(v, -_ANGLE_MAX, _ANGLE_MAX):
                logger.warning("Orientation out of range: %s=%s", key, v)
                return False

        return True


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_float(v: Any, default: float = 0.0) -> float:  # noqa: ANN401
    """Convert *v* to a finite float, falling back to *default*."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if math.isnan(f) or math.isinf(f):
        return default
    return f


def _is_finite_and_in_range(v: Any, lo: float, hi: float) -> bool:  # noqa: ANN401
    """Return True iff *v* is a finite number within [lo, hi]."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    if math.isnan(f) or math.isinf(f):
        return False
    return lo <= f <= hi
