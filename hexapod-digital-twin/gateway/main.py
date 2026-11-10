"""
gateway/main.py

Central entry point for the Hexapod Digital Twin Python Gateway.
Launches:
- FastAPI REST server
- ESP32 Telemetry Receiver (WS :8765)
- Visualizer Broadcaster (WS :8080)
- Webots Controller Bridge (TCP :8766)
"""

from __future__ import annotations

import asyncio
import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directories to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gateway.config.settings import Settings
from gateway.services.safety import SafetySystem
from gateway.services.recorder import TelemetryRecorder
from gateway.services.twin_state_manager import TwinStateManager
from gateway.services.esp32_receiver import ESP32Receiver
from gateway.services.client_broadcaster import ClientBroadcaster
from gateway.services.webots_bridge import WebotsBridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("HexapodGateway")

settings = Settings()
safety = SafetySystem(watchdog_timeout_s=settings.watchdog_timeout_s)
recorder = TelemetryRecorder(recording_dir=settings.recording_dir)
state_manager = TwinStateManager(safety=safety, recorder=recorder)

esp32_receiver = ESP32Receiver(host=settings.gateway_host, port=settings.esp32_port)
broadcaster = ClientBroadcaster(host=settings.gateway_host, port=settings.client_port)
webots_bridge = WebotsBridge(host=settings.gateway_host, port=settings.webots_port)


async def broadcast_loop():
    """Authoritative broadcast loop running at ~40-50 Hz."""
    while True:
        try:
            # Update health metrics
            state_manager.update_health(
                esp32_connected=esp32_receiver.is_connected(),
                webots_connected=webots_bridge.is_connected(),
                client_count=broadcaster.get_client_count(),
            )
            # Check watchdog
            safety.check_watchdog(esp32_receiver.is_connected())

            current_state = state_manager.get_state()

            # Forward virtual servo targets to Webots if connected
            if webots_bridge.is_connected():
                await webots_bridge.send_control(
                    current_state.virtualServos,
                    emergency_stop=current_state.emergencyStop,
                )

            # Broadcast authoritative state to Three.js, Ursina, Pygame
            await broadcaster.broadcast(current_state)
        except Exception as ex:
            logger.error(f"[BROADCAST LOOP] Error: {ex}")

        await asyncio.sleep(0.025)  # 40 Hz


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("   HEXAPOD REAL-TIME DIGITAL TWIN GATEWAY         ")
    logger.info("==================================================")
    logger.info(f" ESP32 Ingestion  : ws://{settings.gateway_host}:{settings.esp32_port}")
    logger.info(f" Clients Broadcast: ws://{settings.gateway_host}:{settings.client_port}")
    logger.info(f" Webots TCP Bridge: {settings.gateway_host}:{settings.webots_port}")
    logger.info("==================================================")

    # Wire up callbacks
    esp32_receiver.set_telemetry_callback(state_manager.ingest_esp32_telemetry)
    broadcaster.set_command_handler(state_manager.handle_command)
    webots_bridge.set_state_callback(state_manager.apply_webots_state)

    # Start networking services
    await esp32_receiver.start()
    await broadcaster.start()
    await webots_bridge.start()

    # Launch background broadcast worker
    worker_task = asyncio.create_task(broadcast_loop())

    yield

    worker_task.cancel()
    await esp32_receiver.stop()
    await broadcaster.stop()
    await webots_bridge.stop()
    logger.info("Gateway shutdown complete.")


app = FastAPI(title="Hexapod Digital Twin Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    command: str
    params: dict = {}


@app.get("/health")
def get_health():
    return {
        "status": "online",
        "esp32_connected": esp32_receiver.is_connected(),
        "webots_connected": webots_bridge.is_connected(),
        "clients_connected": broadcaster.get_client_count(),
        "emergency_stop": safety.is_estop(),
    }


@app.get("/state")
def get_state():
    return state_manager.get_state().model_dump()


@app.post("/command")
async def post_command(req: CommandRequest):
    res = state_manager.handle_command(req.model_dump())
    # If it is a hardware command or calibrate, forward to ESP32
    if req.command in ("CALIBRATE_IMU", "RESET_YAW", "CENTER_SERVO", "EMERGENCY_STOP"):
        await esp32_receiver.send_command(req.model_dump())
    return res


@app.post("/recordings/start")
def start_recording():
    recorder.start_recording()
    return {"status": "recording_started"}


@app.post("/recordings/stop")
def stop_recording():
    count = recorder.stop_recording()
    json_path = recorder.export_json()
    csv_path = recorder.export_csv()
    return {"status": "recording_stopped", "frames": count, "json": json_path, "csv": csv_path}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
