"""
gateway/services/client_broadcaster.py

WebSocket broadcaster service for client visualizers (Three.js, Ursina, Pygame).
Broadcasts authoritative DigitalTwinState at 25-50 Hz and receives client commands.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Set, Callable, Optional, Any

import websockets
from websockets.server import WebSocketServerProtocol

from gateway.models.twin_state import DigitalTwinState

logger = logging.getLogger(__name__)


class ClientBroadcaster:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self._clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._command_handler: Optional[Callable[[dict], Any]] = None

    def set_command_handler(self, handler: Callable[[dict], Any]) -> None:
        self._command_handler = handler

    def get_client_count(self) -> int:
        return len(self._clients)

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._server = await websockets.serve(self._handle_client, self.host, self.port)
        logger.info(f"[CLIENT BROADCASTER] WebSocket server listening on ws://{self.host}:{self.port}")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str = "/") -> None:
        self._clients.add(websocket)
        logger.info(f"[CLIENT BROADCASTER] New visualizer client connected (Total: {len(self._clients)})")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if self._command_handler:
                        res = self._command_handler(data)
                        if asyncio.iscoroutine(res):
                            await res
                except Exception as ex:
                    logger.warning(f"[CLIENT BROADCASTER] Error handling client command: {ex}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.info(f"[CLIENT BROADCASTER] Client disconnected (Remaining: {len(self._clients)})")

    async def broadcast(self, state: DigitalTwinState) -> None:
        """Broadcast state JSON to all connected visualizers."""
        if not self._clients:
            return
        payload = state.to_broadcast_json()
        dead = set()
        for client in self._clients:
            try:
                await client.send(payload)
            except Exception:
                dead.add(client)
        self._clients.difference_update(dead)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
