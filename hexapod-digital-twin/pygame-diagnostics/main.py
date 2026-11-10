"""
pygame-diagnostics/main.py

Lightweight engineering diagnostic console for the Hexapod Digital Twin.
Features:
- Live telemetry ingestion via WebSocket
- Real-time rolling pitch/roll/servo plots
- System status indicators
- Industrial command panel (Calibrate, Reset Yaw, Center Servo, E-STOP)
"""

import sys
import json
import threading
import asyncio
import requests
import pygame
import websockets

from widgets.status_panel import StatusPanelWidget
from widgets.imu_display import ImuDisplayWidget
from widgets.servo_display import ServoDisplayWidget
from widgets.graph_widget import GraphWidget
from widgets.button_widget import ButtonWidget

GATEWAY_WS = "ws://localhost:8080"
GATEWAY_HTTP = "http://localhost:8000/command"

# Thread-safe global state
twin_state = {}
state_lock = threading.Lock()

def ws_worker():
    async def run():
        while True:
            try:
                async with websockets.connect(GATEWAY_WS) as ws:
                    async for msg in ws:
                        try:
                            data = json.loads(msg)
                            with state_lock:
                                twin_state.update(data)
                        except Exception:
                            pass
            except Exception:
                await asyncio.sleep(2.0)
    asyncio.run(run())

def send_command(cmd_name: str, params=None):
    if params is None:
        params = {}
    def req():
        try:
            requests.post(GATEWAY_HTTP, json={"command": cmd_name, "params": params}, timeout=1.0)
        except Exception:
            pass
    threading.Thread(target=req, daemon=True).start()

def main():
    pygame.init()
    pygame.display.set_caption("HEXAPOD DIGITAL TWIN — DIAGNOSTIC CONSOLE")
    screen = pygame.display.set_mode((1000, 600))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 13)

    # Launch background receiver
    t = threading.Thread(target=ws_worker, daemon=True)
    t.start()

    status_widget = StatusPanelWidget((20, 20, 300, 130))
    imu_widget = ImuDisplayWidget((20, 160, 300, 130))
    servo_widget = ServoDisplayWidget((20, 300, 300, 100))
    graph_widget = GraphWidget((340, 20, 640, 380), "LIVE ATTITUDE HISTORY: PITCH (CYAN) & ROLL (GREEN)")

    buttons = [
        ButtonWidget((20, 420, 140, 36), "CALIBRATE IMU", lambda: send_command("CALIBRATE_IMU")),
        ButtonWidget((180, 420, 140, 36), "RESET YAW", lambda: send_command("RESET_YAW")),
        ButtonWidget((20, 470, 140, 36), "CENTER SERVO", lambda: send_command("CENTER_SERVO")),
        ButtonWidget((180, 470, 140, 36), "MIRROR 18", lambda: send_command("ENABLE_MIRROR_18")),
        ButtonWidget((340, 420, 640, 46), "🛑 EMERGENCY STOP", lambda: send_command("EMERGENCY_STOP"), color=(180, 20, 20)),
        ButtonWidget((340, 480, 640, 36), "RESET EMERGENCY STOP", lambda: send_command("RESET_EMERGENCY_STOP"), color=(40, 90, 40)),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for btn in buttons:
                btn.handle_event(event)

        with state_lock:
            s = dict(twin_state)

        # Update graph data
        orient = s.get("orientation", {})
        p = orient.get("pitch", 0.0)
        r = orient.get("roll", 0.0)
        sv = s.get("physicalServo", {}).get("angle", 90)
        graph_widget.add_point(p, r, sv)

        # Render
        screen.fill((20, 20, 20))
        status_widget.draw(screen, font, s)
        imu_widget.draw(screen, font, s)
        servo_widget.draw(screen, font, s)
        graph_widget.draw(screen, font)

        for btn in buttons:
            btn.draw(screen, font)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
