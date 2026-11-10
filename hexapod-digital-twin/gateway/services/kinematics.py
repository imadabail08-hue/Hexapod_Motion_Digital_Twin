"""
gateway/services/kinematics.py

Analytical forward and inverse kinematics for a single hexapod leg.

Coordinate frame (body-relative, per leg attachment point):
  x — forward along the leg's coxa axis
  y — lateral (perpendicular to coxa, in the horizontal plane)
  z — vertical (up = positive)

Joint angles are in degrees throughout the public interface.

All segment lengths are loaded from shared/config/robot_params.yaml.
If the YAML is unavailable the class falls back to module-level defaults.
"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default segment lengths (metres) — used when YAML cannot be loaded.
# [PLACEHOLDER — not physically measured]
# ---------------------------------------------------------------------------
_DEFAULT_COXA_LEN: float = 0.053
_DEFAULT_FEMUR_LEN: float = 0.066
_DEFAULT_TIBIA_LEN: float = 0.132

DEFAULT_LEG_DIMS = (_DEFAULT_COXA_LEN, _DEFAULT_FEMUR_LEN, _DEFAULT_TIBIA_LEN)


def _load_params_yaml() -> dict:  # type: ignore[type-arg]
    """Attempt to load robot_params.yaml and return its parsed content.

    Returns an empty dict on any failure so callers can use fallback values.
    """
    try:
        import yaml  # type: ignore[import-not-found]

        candidates = [
            Path(__file__).parent.parent.parent / "shared" / "config" / "robot_params.yaml",
            Path("shared") / "config" / "robot_params.yaml",
        ]
        for path in candidates:
            if path.exists():
                with open(path, "r", encoding="utf-8") as fh:
                    return yaml.safe_load(fh) or {}
        logger.warning("robot_params.yaml not found — using built-in defaults")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load robot_params.yaml: %s — using defaults", exc)
    return {}


def _get_segment_lengths() -> tuple[float, float, float]:
    """Return (coxa_len, femur_len, tibia_len) in metres."""
    params = _load_params_yaml()
    coxa_len = float(params.get("coxa", {}).get("length_m", _DEFAULT_COXA_LEN))
    femur_len = float(params.get("femur", {}).get("length_m", _DEFAULT_FEMUR_LEN))
    tibia_len = float(params.get("tibia", {}).get("length_m", _DEFAULT_TIBIA_LEN))
    return coxa_len, femur_len, tibia_len


class LegKinematics:
    """Analytical forward/inverse kinematics for one hexapod leg.

    The leg has three revolute joints in the order coxa → femur → tibia,
    modelled in the 2-D plane defined by the coxa rotation axis (Z) and the
    leg reach direction.

    Attributes:
        coxa_len:  Length of the coxa segment (m).
        femur_len: Length of the femur segment (m).
        tibia_len: Length of the tibia segment (m).
    """

    def __init__(
        self,
        coxa_len: Optional[float] = None,
        femur_len: Optional[float] = None,
        tibia_len: Optional[float] = None,
    ) -> None:
        default_c, default_f, default_t = _get_segment_lengths()
        self.coxa_len: float = coxa_len if coxa_len is not None else default_c
        self.femur_len: float = femur_len if femur_len is not None else default_f
        self.tibia_len: float = tibia_len if tibia_len is not None else default_t

        logger.debug(
            "LegKinematics: coxa=%.4fm femur=%.4fm tibia=%.4fm",
            self.coxa_len,
            self.femur_len,
            self.tibia_len,
        )

    # ------------------------------------------------------------------
    # Forward kinematics
    # ------------------------------------------------------------------

    def forward_kinematics(
        self,
        coxa_deg: float,
        femur_deg: float,
        tibia_deg: float,
    ) -> tuple[float, float, float]:
        """Compute foot position from joint angles.

        Uses direct trigonometric expansion of the kinematic chain.

        Args:
            coxa_deg:  Coxa joint angle in degrees (swing around Z-axis).
            femur_deg: Femur joint angle in degrees (vertical lift around X).
            tibia_deg: Tibia joint angle in degrees (extension around X,
                       inverted direction per JOINT_CONFIG).

        Returns:
            ``(x, y, z)`` foot position in the leg's local frame (metres).
        """
        coxa_rad = math.radians(coxa_deg)
        femur_rad = math.radians(femur_deg)
        # Tibia direction is -1 per joint config
        tibia_rad = math.radians(-tibia_deg)

        # 2-D reach in the sagittal plane (before coxa rotation)
        reach = (
            self.coxa_len
            + self.femur_len * math.cos(femur_rad)
            + self.tibia_len * math.cos(femur_rad + tibia_rad)
        )
        z = (
            self.femur_len * math.sin(femur_rad)
            + self.tibia_len * math.sin(femur_rad + tibia_rad)
        )

        # Project reach into x-y plane using coxa rotation
        x = reach * math.cos(coxa_rad)
        y = reach * math.sin(coxa_rad)

        return x, y, z

    # ------------------------------------------------------------------
    # Inverse kinematics
    # ------------------------------------------------------------------

    def inverse_kinematics(
        self,
        target_x: float,
        target_y: float,
        target_z: float,
    ) -> Optional[tuple[float, float, float]]:
        """Compute joint angles to reach a 3-D foot position.

        Uses closed-form geometric IK for a 3-DOF planar leg.

        Args:
            target_x: Desired foot X in the leg's local frame (m).
            target_y: Desired foot Y in the leg's local frame (m).
            target_z: Desired foot Z in the leg's local frame (m, up+).

        Returns:
            ``(coxa_deg, femur_deg, tibia_deg)`` if reachable, else *None*.
        """
        # Coxa angle — horizontal swing
        coxa_rad = math.atan2(target_y, target_x)
        coxa_deg = math.degrees(coxa_rad)

        # Horizontal reach after coxa rotation (distance from coxa pivot to
        # the point directly below the femur pivot)
        horizontal_reach = math.sqrt(target_x ** 2 + target_y ** 2) - self.coxa_len

        # 2-D IK in the sagittal plane (reach, z)
        d = math.sqrt(horizontal_reach ** 2 + target_z ** 2)

        if d > (self.femur_len + self.tibia_len):
            logger.debug(
                "IK: target unreachable — distance %.4f m > max reach %.4f m",
                d,
                self.femur_len + self.tibia_len,
            )
            return None

        if d < abs(self.femur_len - self.tibia_len):
            logger.debug(
                "IK: target too close — distance %.4f m < min reach %.4f m",
                d,
                abs(self.femur_len - self.tibia_len),
            )
            return None

        # Law of cosines for femur and tibia angles
        cos_tibia = (d ** 2 - self.femur_len ** 2 - self.tibia_len ** 2) / (
            2.0 * self.femur_len * self.tibia_len
        )
        tibia_rad = math.acos(self._safe_acos(cos_tibia))

        cos_femur_inner = (d ** 2 + self.femur_len ** 2 - self.tibia_len ** 2) / (
            2.0 * d * self.femur_len
        )
        alpha = math.acos(self._safe_acos(cos_femur_inner))
        gamma = math.atan2(target_z, horizontal_reach)
        femur_rad = gamma + alpha

        femur_deg = math.degrees(femur_rad)
        # Tibia angle in our convention (direction=-1 → negate)
        tibia_deg = -math.degrees(tibia_rad)

        return coxa_deg, femur_deg, tibia_deg

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_acos(v: float) -> float:
        """Clamp *v* to [-1, 1] before passing to ``math.acos``.

        Prevents domain errors caused by floating-point rounding.

        Args:
            v: Input value, ideally in [-1, 1].

        Returns:
            *v* clamped to [-1, 1].
        """
        return max(-1.0, min(1.0, v))
