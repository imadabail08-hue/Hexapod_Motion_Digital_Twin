"""
gateway/services/safety.py

Industrial safety supervisor:
- Emergency stop (E-STOP) state management
- Software servo limit enforcement
- Watchdog timer for connection timeouts
- Telemetry validation and sanitization
"""

from __future__ import annotations

import math
import time
from typing import Optional

from shared.protocol.servo_map import JOINT_CONFIG


class SafetySystem:
    def __init__(self, watchdog_timeout_s: float = 5.0) -> None:
        self.watchdog_timeout_s = watchdog_timeout_s
        self._estop: bool = False
        self._last_packet_time: float = time.time()

    def emergency_stop(self) -> None:
        """Latch the emergency stop."""
        self._estop = True

    def reset_emergency_stop(self) -> None:
        """Reset the emergency stop latch."""
        self._estop = False

    def is_estop(self) -> bool:
        """Check whether E-STOP is currently active."""
        return self._estop

    def update_watchdog(self) -> None:
        """Update last heartbeat timestamp."""
        self._last_packet_time = time.time()

    def check_watchdog(self, esp32_connected: bool) -> bool:
        """Check if packet timeout occurred. Returns True if timeout occurred."""
        if not esp32_connected:
            return False
        elapsed = time.time() - self._last_packet_time
        if elapsed > self.watchdog_timeout_s:
            self._estop = True
            return True
        return False

    def clamp_servo(self, angle: float, servo_id: int) -> float:
        """Enforce strict min/max limits for a specific servo ID."""
        if math.isnan(angle) or math.isinf(angle):
            return 90.0

        if servo_id in JOINT_CONFIG:
            cfg = JOINT_CONFIG[servo_id]
            # Convert joint angle (-90..90) or servo command (0..180) safely
            # If in 0..180 servo coordinates:
            min_a = 50.0
            max_a = 130.0
        else:
            min_a = 0.0
            max_a = 180.0

        return max(min_a, min(max_a, float(angle)))

    def validate_telemetry(self, packet: dict) -> bool:
        """Validate an incoming raw telemetry dictionary against NaN/Inf and required keys."""
        if not isinstance(packet, dict):
            return False
        if packet.get("type") != "telemetry":
            return False

        imu = packet.get("imu")
        if not isinstance(imu, dict):
            return False

        for k in ("ax", "ay", "az", "gx", "gy", "gz"):
            v = imu.get(k)
            if v is None:
                return False
            try:
                fv = float(v)
                if math.isnan(fv) or math.isinf(fv):
                    return False
                if k.startswith("a") and abs(fv) > 100.0:
                    return False
            except (ValueError, TypeError):
                return False

        return True
