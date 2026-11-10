"""
gateway/services/imu_processor.py

Server-side IMU processing for SIMULATION mode (no physical ESP32 present)
and for supplementary server-side orientation fusion when running alongside
the ESP32.

Provides:
  - ComplementaryFilter  — fuses accelerometer + gyroscope data
  - CalibrationResult    — zero-bias calibration output
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from gateway.models.twin_state import ImuRaw, Orientation

logger = logging.getLogger(__name__)

# Small epsilon to avoid division-by-zero in atan2
_EPS: float = 1e-9


@dataclass
class CalibrationResult:
    """Result of a static zero-bias calibration pass.

    Attributes:
        bias_ax: Accelerometer X bias (m/s²).
        bias_ay: Accelerometer Y bias (m/s²).
        bias_az: Accelerometer Z bias — expected ~9.81 m/s² at rest.
        bias_gx: Gyroscope X zero-rate bias (deg/s).
        bias_gy: Gyroscope Y zero-rate bias (deg/s).
        bias_gz: Gyroscope Z zero-rate bias (deg/s).
        sample_count: Number of samples averaged.
    """

    bias_ax: float = 0.0
    bias_ay: float = 0.0
    bias_az: float = 0.0
    bias_gx: float = 0.0
    bias_gy: float = 0.0
    bias_gz: float = 0.0
    sample_count: int = 0


class ComplementaryFilter:
    """First-order complementary filter for IMU orientation fusion.

    Fuses high-frequency gyroscope integration with low-frequency
    accelerometer tilt estimates to produce stable pitch and roll angles.
    Yaw is integrated from the gyroscope only (no absolute heading source
    unless an external magnetometer is added later).

    Attributes:
        alpha:   Gyroscope trust weight in [0, 1).  Higher values give
                 smoother output at the cost of slower response to real tilt.
        pitch:   Current filtered pitch estimate (deg).
        roll:    Current filtered roll estimate (deg).
        yaw:     Current integrated yaw estimate (deg).
        bias_x:  Gyroscope X bias applied each update (deg/s).
        bias_y:  Gyroscope Y bias applied each update (deg/s).
        bias_z:  Gyroscope Z bias applied each update (deg/s).
    """

    def __init__(self, alpha: float = 0.98) -> None:
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        self.alpha: float = alpha

        self.pitch: float = 0.0
        self.roll: float = 0.0
        self.yaw: float = 0.0

        self.bias_x: float = 0.0
        self.bias_y: float = 0.0
        self.bias_z: float = 0.0

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    @staticmethod
    def calibrate(samples: list[ImuRaw]) -> CalibrationResult:
        """Compute zero-bias offsets from a list of static IMU readings.

        The robot must be perfectly still during calibration.  The
        accelerometer Z bias absorbs gravity (expected ~9.81 m/s²).

        Args:
            samples: List of raw IMU readings taken while stationary.

        Returns:
            :class:`CalibrationResult` with averaged bias values.
        """
        if not samples:
            logger.warning("calibrate() called with empty sample list")
            return CalibrationResult()

        n = len(samples)
        result = CalibrationResult(
            bias_ax=sum(s.ax for s in samples) / n,
            bias_ay=sum(s.ay for s in samples) / n,
            bias_az=sum(s.az for s in samples) / n,
            bias_gx=sum(s.gx for s in samples) / n,
            bias_gy=sum(s.gy for s in samples) / n,
            bias_gz=sum(s.gz for s in samples) / n,
            sample_count=n,
        )
        logger.info(
            "IMU calibration complete (%d samples) — gyro bias: "
            "gx=%.4f gy=%.4f gz=%.4f deg/s",
            n,
            result.bias_gx,
            result.bias_gy,
            result.bias_gz,
        )
        return result

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, raw: ImuRaw, dt: float) -> Orientation:
        """Fuse one IMU sample and return the updated orientation.

        Algorithm:
          1. Subtract gyroscope biases.
          2. Integrate gyroscope to predict new angles (gyro step).
          3. Compute tilt-only pitch/roll from accelerometer (accel step).
          4. Blend: angle = alpha * gyro_angle + (1-alpha) * accel_angle.
          5. Integrate gyroscope Z for yaw (no accel correction).

        Args:
            raw: One raw IMU sample (accelerometer m/s², gyroscope deg/s).
            dt:  Time elapsed since the previous update (seconds).

        Returns:
            Updated :class:`Orientation` with filtered pitch, roll, yaw.
        """
        if dt <= 0.0:
            logger.debug("update() called with dt=%s — skipping", dt)
            return Orientation(pitch=self.pitch, roll=self.roll, yaw=self.yaw)

        # 1. Bias-corrected gyro rates (deg/s → rad/s not needed; we stay in deg)
        gx_corr = raw.gx - self.bias_x
        gy_corr = raw.gy - self.bias_y
        gz_corr = raw.gz - self.bias_z

        # 2. Gyro integration
        pitch_gyro = self.pitch + gx_corr * dt
        roll_gyro = self.roll + gy_corr * dt

        # 3. Accelerometer tilt estimate
        ax, ay, az = raw.ax, raw.ay, raw.az
        accel_magnitude = math.sqrt(ax * ax + ay * ay + az * az)

        if accel_magnitude > _EPS:
            # atan2-based tilt (does not require division by g)
            pitch_accel = math.degrees(math.atan2(ay, math.sqrt(ax * ax + az * az + _EPS)))
            roll_accel = math.degrees(math.atan2(-ax, az + _EPS))
        else:
            # No usable gravity vector — fall back to gyro only
            pitch_accel = pitch_gyro
            roll_accel = roll_gyro

        # 4. Complementary blend
        self.pitch = self.alpha * pitch_gyro + (1.0 - self.alpha) * pitch_accel
        self.roll = self.alpha * roll_gyro + (1.0 - self.alpha) * roll_accel

        # 5. Yaw — gyro integration only, wrapped to (-180, 180]
        self.yaw = _wrap_180(self.yaw + gz_corr * dt)

        return Orientation(pitch=self.pitch, roll=self.roll, yaw=self.yaw)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_yaw(self) -> None:
        """Zero the integrated yaw angle (set current heading as reference)."""
        logger.info("Yaw reset — previous value: %.2f deg", self.yaw)
        self.yaw = 0.0

    def apply_calibration(self, result: CalibrationResult) -> None:
        """Load gyroscope biases from a :class:`CalibrationResult`.

        Args:
            result: Output of :meth:`calibrate`.
        """
        self.bias_x = result.bias_gx
        self.bias_y = result.bias_gy
        self.bias_z = result.bias_gz
        logger.info(
            "Applied IMU calibration — gyro bias: gx=%.4f gy=%.4f gz=%.4f",
            self.bias_x,
            self.bias_y,
            self.bias_z,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _wrap_180(angle: float) -> float:
    """Wrap an angle in degrees to the range (-180, 180]."""
    angle = angle % 360.0
    if angle > 180.0:
        angle -= 360.0
    return angle
