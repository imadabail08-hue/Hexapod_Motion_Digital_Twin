"""
gateway/services/esp32_receiver.py

WebSocket server for ESP32 hardware telemetry ingestion on port 8765.
Relays incoming telemetry frames to TwinStateManager and sends commands to the ESP32.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional, Callable, Any

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class ESP32Receiver:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._server = None
        self._esp32_socket: Optional[WebSocketServerProtocol] = None
        self._telemetry_callback: Optional[Callable[[dict], Any]] = None
        self._connected: bool = False

    def is_connected(self) -> bool:
        return self._connected

    def set_telemetry_callback(self, cb: Callable[[dict], Any]) -> None:
        self._telemetry_callback = cb

    async def start(self) -> None:
        """Start the WebSocket server listening for the ESP32."""
        self._server = await websockets.serve(self._handle_connection, self.host, self.port)
        logger.info(f"[ESP32 RECEIVER] WebSocket listening on ws://{self.host}:{self.port}")

    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str = "/") -> None:
        logger.info(f"[ESP32 RECEIVER] ESP32 connected from {websocket.remote_address}")
        self._esp32_socket = websocket
        self._connected = True

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if self._telemetry_callback:
                        res = self._telemetry_callback(data)
                        if asyncio.iscoroutine(res):
                            await res
                except Exception as ex:
                    logger.warning(f"[ESP32 RECEIVER] Error decoding telemetry: {ex}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._connected = False
            self._esp32_socket = None
            logger.info(f"[ESP32 RECEIVER] ESP32 disconnected")

    async def send_command(self, cmd: dict) -> bool:
        """Send a JSON command back to the ESP32 hardware."""
        if not self._connected or not self._esp32_socket:
            return False
        try:
            await self._esp32_socket.send(json.dumps(cmd))
            return True
        except Exception as ex:
            logger.warning(f"[ESP32 RECEIVER] Error sending command: {ex}")
            return False

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
