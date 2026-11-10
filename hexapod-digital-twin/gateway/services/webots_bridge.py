"""
gateway/services/webots_bridge.py

TCP Bridge for bi-directional communication between Python Gateway and Webots controller.
Listens on TCP port (default 8766) and accepts the Webots controller connection.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)


class WebotsBridge:
    def __init__(self, host: str = "0.0.0.0", port: int = 8766) -> None:
        self.host = host
        self.port = port
        self._server: Optional[asyncio.Server] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._connected: bool = False
        self._on_state_received: Optional[Callable[[Dict[str, Any]], None]] = None

    def is_connected(self) -> bool:
        return self._connected

    def set_state_callback(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        self._on_state_received = cb

    async def start(self) -> None:
        """Start the TCP server listening for the Webots controller."""
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"[WEBOTS BRIDGE] TCP Server listening on {self.host}:{self.port}")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.info(f"[WEBOTS BRIDGE] Controller connected from {addr}")
        self._reader = reader
        self._writer = writer
        self._connected = True

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    payload = json.loads(line.decode("utf-8").strip())
                    if self._on_state_received:
                        self._on_state_received(payload)
                except Exception as ex:
                    logger.warning(f"[WEBOTS BRIDGE] Failed to parse JSON: {ex}")
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            logger.warning(f"[WEBOTS BRIDGE] Connection error: {ex}")
        finally:
            self._connected = False
            self._writer = None
            self._reader = None
            logger.info(f"[WEBOTS BRIDGE] Controller disconnected")

    async def send_control(self, servo_targets: List[float], emergency_stop: bool = False) -> None:
        """Send target joint positions to the Webots controller."""
        if not self._connected or not self._writer:
            return
        msg = {
            "type": "control",
            "servoTargets": servo_targets,
            "emergencyStop": emergency_stop,
        }
        try:
            data = json.dumps(msg) + "\n"
            self._writer.write(data.encode("utf-8"))
            await self._writer.drain()
        except Exception as ex:
            logger.warning(f"[WEBOTS BRIDGE] Failed to send control targets: {ex}")
            self._connected = False

    async def stop(self) -> None:
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        if self._server:
            self._server.close()
            await self._server.wait_closed()
