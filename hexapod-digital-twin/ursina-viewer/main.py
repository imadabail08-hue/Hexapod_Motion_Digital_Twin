"""
Hexapod Digital Twin — Ursina Engineering Viewer
=================================================
Secondary 3D debug/engineering viewer.

Consumes DigitalTwinState JSON from the Gateway WebSocket and
renders the hexapod body + 18 leg joints in real time.

Design principle
----------------
This module contains NO robot logic — it is a pure visualisation
consumer.  All kinematics decisions remain in the Gateway.

Controls
--------
  1      → Top-down view
  2      → Front view
  3      → Left side view
  R      → Reset isometric camera
  Mouse  → Orbit (right-click drag) + Pan (middle-click drag)
  Scroll → Zoom
"""

from ursina import (
    Ursina, Entity, Text, Vec3, color,
    DirectionalLight, AmbientLight,
    camera, window, held_keys, mouse, application
)
import websockets
import asyncio
import threading
import json
import math

# Local modules
from robot.hexapod_entity import HexapodEntity
from robot.frame_transforms import imu_to_ursina

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GATEWAY_WS_URL = "ws://localhost:8080"
UPDATE_INTERVAL = 1.0 / 30.0   # 30 FPS display target


# ---------------------------------------------------------------------------
# Shared state (populated by WS thread, consumed by Ursina update())
# ---------------------------------------------------------------------------
twin_state: dict = {}
state_lock = threading.Lock()
ws_connected = threading.Event()


# ---------------------------------------------------------------------------
# WebSocket background thread
# ---------------------------------------------------------------------------
def ws_thread_fn():
    """
    WebSocket receive loop running in a daemon thread.
    Reconnects automatically on disconnect or error.
    """
    async def _connect():
        while True:
            try:
                async with websockets.connect(
                    GATEWAY_WS_URL,
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    print(f"[URSINA] ✓ Connected to Gateway — {GATEWAY_WS_URL}")
                    ws_connected.set()
                    async for msg in ws:
                        try:
                            data = json.loads(msg)
                            with state_lock:
                                twin_state.update(data)
                        except json.JSONDecodeError:
                            pass
                ws_connected.clear()
            except Exception as exc:
                ws_connected.clear()
                print(f"[URSINA] WS error: {exc!r} — retrying in 2 s")
                await asyncio.sleep(2.0)

    asyncio.run(_connect())


# Launch WS thread before Ursina app starts
_ws_thread = threading.Thread(target=ws_thread_fn, daemon=True)
_ws_thread.start()


# ---------------------------------------------------------------------------
# Ursina application
# ---------------------------------------------------------------------------
app = Ursina(
    title="Hexapod Digital Twin — Engineering Viewer",
    borderless=False,
    fullscreen=False,
    size=(1280, 720),
)

window.color = color.color(0, 0, 0.07, 1)   # near-black

# Camera — isometric-ish starting position
camera.position = Vec3(1.5, 1.5, -1.8)
camera.look_at(Vec3(0, 0, 0))

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
DirectionalLight(y=2, z=-1, shadows=True)
AmbientLight(color=color.rgba(50, 50, 60, 255))

# ---------------------------------------------------------------------------
# Ground grid
# ---------------------------------------------------------------------------
grid = Entity(
    model="plane",
    scale=4,
    color=color.color(0, 0, 0.10, 0.85),
    y=-0.025,
)

# Grid lines (simple cross-hatch overlay)
for i in range(-4, 5):
    Entity(
        model="cube",
        scale=(8, 0.001, 0.002),
        position=(0, -0.024, i * 0.5),
        color=color.color(0, 0, 0.2, 0.5),
    )
    Entity(
        model="cube",
        scale=(0.002, 0.001, 8),
        position=(i * 0.5, -0.024, 0),
        color=color.color(0, 0, 0.2, 0.5),
    )

# ---------------------------------------------------------------------------
# World frame axis indicators (small arrows at origin)
# ---------------------------------------------------------------------------
# X axis — Red
Entity(model="cube", scale=(0.3, 0.005, 0.005), position=(0.15, 0, 0), color=color.red)
# Y axis — Green
Entity(model="cube", scale=(0.005, 0.3, 0.005), position=(0, 0.15, 0), color=color.green)
# Z axis — Blue
Entity(model="cube", scale=(0.005, 0.005, 0.3), position=(0, 0, 0.15), color=color.blue)

# Axis labels
Text(text="X", position=(0.18, 0, 0), scale=0.8, color=color.red)
Text(text="Y", position=(0, 0.18, 0), scale=0.8, color=color.green)
Text(text="Z", position=(0, 0, 0.18), scale=0.8, color=color.blue)

# ---------------------------------------------------------------------------
# Hexapod 3D entity
# ---------------------------------------------------------------------------
hexapod = HexapodEntity()

# ---------------------------------------------------------------------------
# HUD overlay texts
# ---------------------------------------------------------------------------
_TEXT_X  = -0.85
_TEXT_Y0 = 0.47

def _make_label(text: str, y_offset: int, clr=color.white) -> Text:
    return Text(
        text=text,
        position=(_TEXT_X, _TEXT_Y0 - y_offset * 0.055),
        scale=1.15,
        color=clr,
    )

hud_title    = _make_label("HEXAPOD DIGITAL TWIN", 0, color.orange)
pitch_text   = _make_label("Pitch:  0.0°",          1, color.cyan)
roll_text    = _make_label("Roll:   0.0°",           2, color.lime)
yaw_text     = _make_label("Yaw:    0.0° [DRIFT]",  3, color.yellow)
mode_text    = _make_label("Mode:   --",             4, color.white)
sync_text    = _make_label("Sync:   --",             5, color.gray)
esp32_text   = _make_label("ESP32:  --",             6, color.gray)
webots_text  = _make_label("Webots: --",             7, color.gray)
fps_text     = _make_label("FPS:    --",             8, color.color(0, 0, 0.55, 1))

# Connection dot
conn_dot = Entity(
    model="circle",
    scale=0.015,
    position=(-0.92, _TEXT_Y0 - 5 * 0.055),
    color=color.gray,
)

# ---------------------------------------------------------------------------
# Sync-colour mapping
# ---------------------------------------------------------------------------
_SYNC_COLORS = {
    "GOOD":     color.lime,
    "DEGRADED": color.yellow,
    "LOST":     color.red,
    "UNKNOWN":  color.gray,
}

# ---------------------------------------------------------------------------
# Camera orbit state
# ---------------------------------------------------------------------------
_orbit_speed = 60.0   # degrees/second per pixel
_cam_yaw   = -25.0
_cam_pitch =  25.0
_cam_dist  =   2.2

# ---------------------------------------------------------------------------
# update() — called every frame by Ursina
# ---------------------------------------------------------------------------
def update():
    global _cam_yaw, _cam_pitch, _cam_dist

    # --- Right-click orbit ---
    if held_keys["right mouse"]:
        _cam_yaw   -= mouse.velocity[0] * 120
        _cam_pitch -= mouse.velocity[1] * 120
        _cam_pitch  = max(-80, min(80, _cam_pitch))

    # --- Scroll zoom ---
    if mouse.wheel and mouse.wheel != 0:
        _cam_dist -= mouse.wheel * 0.15
        _cam_dist  = max(0.4, min(6.0, _cam_dist))

    # Recompute camera position from spherical coords
    yaw_r   = math.radians(_cam_yaw)
    pitch_r = math.radians(_cam_pitch)
    cx = _cam_dist * math.cos(pitch_r) * math.sin(yaw_r)
    cy = _cam_dist * math.sin(pitch_r)
    cz = _cam_dist * math.cos(pitch_r) * math.cos(yaw_r)
    camera.position = Vec3(cx, cy, cz)
    camera.look_at(Vec3(0, 0.03, 0))

    # --- Consume latest twin state ---
    with state_lock:
        s = dict(twin_state)

    if not s:
        fps_text.text = f"FPS:    {int(1.0 / max(application.time_scale, 0.001))}"
        return

    # Orientation
    orientation = s.get("orientation", {})
    pitch = float(orientation.get("pitch", 0.0))
    roll  = float(orientation.get("roll",  0.0))
    yaw   = float(orientation.get("yaw",   0.0))

    # Apply body orientation (IMU → Ursina frame)
    ux, uy, uz = imu_to_ursina(pitch, roll, yaw)
    hexapod.body.rotation = Vec3(ux, uy, uz)

    # Apply 18 joint angles
    virtual_servos = s.get("virtualServos", [90.0] * 18)
    hexapod.apply_servo_angles(virtual_servos)

    # Foot contact colours
    foot_contacts = s.get("footContacts", {})
    hexapod.update_foot_contacts(foot_contacts)

    # --- HUD updates ---
    pitch_text.text = f"Pitch:  {pitch:+.1f}°"
    roll_text.text  = f"Roll:   {roll:+.1f}°"
    yaw_text.text   = f"Yaw:    {yaw:+.1f}°  [GYRO-INTEGRATED]"
    mode_text.text  = f"Mode:   {s.get('mode', '--')}"

    health = s.get("twinHealth", {})
    sync   = health.get("syncStatus", "UNKNOWN")
    sync_text.text  = f"Sync:   {sync}"
    sync_text.color = _SYNC_COLORS.get(sync, color.gray)
    conn_dot.color  = _SYNC_COLORS.get(sync, color.gray)

    conn = s.get("connection", {})
    esp32_on  = conn.get("esp32", False)
    webots_on = conn.get("webots", False)
    esp32_text.text  = f"ESP32:  {'● ONLINE' if esp32_on  else '○ OFFLINE'}"
    esp32_text.color = color.lime if esp32_on  else color.red
    webots_text.text = f"Webots: {'● RUNNING' if webots_on else '○ STOPPED'}"
    webots_text.color = color.lime if webots_on else color.red

    rtf = s.get("rtf", 0.0)
    fps_text.text = f"RTF:    {rtf:.2f}x"


# ---------------------------------------------------------------------------
# input() — keyboard shortcuts
# ---------------------------------------------------------------------------
def input(key: str):
    global _cam_yaw, _cam_pitch, _cam_dist
    if key == "1":        # Top-down
        _cam_yaw, _cam_pitch, _cam_dist = 0, 89, 2.0
    elif key == "2":      # Front
        _cam_yaw, _cam_pitch, _cam_dist = 0, 10, 2.2
    elif key == "3":      # Left side
        _cam_yaw, _cam_pitch, _cam_dist = 90, 10, 2.2
    elif key == "4":      # Right side
        _cam_yaw, _cam_pitch, _cam_dist = -90, 10, 2.2
    elif key in ("r", "R"):  # Reset isometric
        _cam_yaw, _cam_pitch, _cam_dist = -25, 25, 2.2
    elif key == "escape":
        application.quit()


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
print("[URSINA] Hexapod Engineering Viewer started")
print("  Keys: 1=Top  2=Front  3=Left  4=Right  R=Reset")
print("  Mouse: Right-drag=Orbit  Scroll=Zoom")
app.run()
