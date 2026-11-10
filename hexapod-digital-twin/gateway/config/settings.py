"""
gateway/config/settings.py

Pydantic-Settings based configuration for the Digital Twin Gateway.
All values can be overridden via environment variables prefixed with
GATEWAY_ (e.g. GATEWAY_ESP32_PORT=9000) or via a .env file.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the gateway service.

    Attributes:
        gateway_host:        Bind address for all listening sockets.
        esp32_port:          WebSocket port for the ESP32 firmware connection.
        client_port:         WebSocket port for visualiser client connections.
        webots_port:         TCP port for the Webots controller bridge.
        complementary_alpha: Complementary filter weight for IMU fusion
                             (0 < alpha < 1; higher = trust gyro more).
        sync_good_ms:        Maximum packet age (ms) for SYNC_GOOD status.
        sync_degraded_ms:    Maximum packet age (ms) for SYNC_DEGRADED status
                             (anything older → SYNC_LOST).
        watchdog_timeout_s:  Seconds without ESP32 data before emergency stop.
        recording_dir:       Directory path for telemetry recording files.
        log_level:           Python logging level string.
    """

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Network ─────────────────────────────────────────────────────────────
    gateway_host: str = "0.0.0.0"
    esp32_port: int = 8765
    client_port: int = 8080
    webots_port: int = 8766

    # ── IMU filter ───────────────────────────────────────────────────────────
    complementary_alpha: float = 0.98

    # ── Sync health thresholds ───────────────────────────────────────────────
    sync_good_ms: int = 150
    sync_degraded_ms: int = 500

    # ── Safety ──────────────────────────────────────────────────────────────
    watchdog_timeout_s: float = 5.0

    # ── Storage ─────────────────────────────────────────────────────────────
    recording_dir: str = "recordings"

    # ── Logging ─────────────────────────────────────────────────────────────
    log_level: str = "INFO"


# Module-level singleton — import this everywhere.
settings = Settings()
