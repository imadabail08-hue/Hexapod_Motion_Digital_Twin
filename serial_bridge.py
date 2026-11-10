"""
Universal Digital Twin Gateway (Wokwi Simulator + Hardware COM)
Connects to:
1. Wokwi Simulator TCP Port 4000 (VS Code Wokwi extension rfc2217ServerPort)
2. Virtual / Physical COM ports (COM4, COM5, COM8, etc.)
Broadcasts real-time telemetry to the Three.js Electron Digital Twin on ws://127.0.0.1:8765
"""

import sys
import time
import json
import socket
import asyncio
import threading
import serial
import serial.tools.list_ports

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

CONNECTED_CLIENTS = set()
LATEST_TELEMETRY = {
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0,
    "servo": 90,
    "source": "Searching...",
    "timestamp": time.time(),
    "connected": False
}

def is_port_in_use(port=8765):
    """Check if the WebSocket port is already running in another process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_wokwi_tcp(host="127.0.0.1", port=4000):
    """Check if Wokwi RFC2217 TCP server is active."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

def find_serial_port():
    """Auto-detect any available serial port."""
    ports = list(serial.tools.list_ports.comports())
    # Priority: COM8, COM5, COM4, or any USB UART
    for p in ports:
        if "COM8" in p.device:
            return p.device
    for p in ports:
        if any(target in p.device for target in ["COM5", "COM4"]):
            return p.device
    for p in ports:
        if any(keyword in p.description.lower() for keyword in ["ch340", "cp210", "ftdi", "usb-serial", "uart", "esp"]):
            return p.device
    if ports:
        return ports[0].device
    return None

def parse_telemetry_line(line: str):
    """Parse JSON or text telemetry packet."""
    global LATEST_TELEMETRY
    line = line.strip()
    if not line:
        return

    # Parse JSON: {"roll":..., "pitch":..., "yaw":..., "servo":...}
    if line.startswith("{") and line.endswith("}"):
        try:
            data = json.loads(line)
            LATEST_TELEMETRY.update(data)
            LATEST_TELEMETRY["timestamp"] = time.time()
            LATEST_TELEMETRY["connected"] = True
            return
        except json.JSONDecodeError:
            pass

    # Parse fallback text
    if "Pitch" in line and "Servo" in line:
        try:
            parts = line.split("|")
            pitch_val = float(parts[0].replace("Pitch :", "").replace("Pitch:", "").replace("deg", "").strip())
            servo_val = int(parts[1].replace("Servo :", "").replace("Servo:", "").strip())
            LATEST_TELEMETRY["pitch"] = pitch_val
            LATEST_TELEMETRY["servo"] = servo_val
            LATEST_TELEMETRY["timestamp"] = time.time()
            LATEST_TELEMETRY["connected"] = True
        except Exception:
            pass

def telemetry_worker():
    """Continuously tries Wokwi TCP port 4000, then fallback COM ports."""
    global LATEST_TELEMETRY
    while True:
        # 1. Try Wokwi Simulator TCP 4000
        if check_wokwi_tcp("127.0.0.1", 4000):
            print("[GATEWAY] Wokwi Simulator detected on TCP port 4000! Connecting...", flush=True)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect(("127.0.0.1", 4000))
                print("[GATEWAY] CONNECTED to Wokwi Simulator! Streaming real-time telemetry...", flush=True)
                LATEST_TELEMETRY["connected"] = True
                LATEST_TELEMETRY["source"] = "Wokwi Simulator (TCP 4000)"

                buf = ""
                while True:
                    data = s.recv(1024).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    buf += data
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        parse_telemetry_line(line)
            except Exception as e:
                print(f"[GATEWAY] Wokwi session ended: {e}", flush=True)
                LATEST_TELEMETRY["connected"] = False

        # 2. Try Serial COM ports (COM4, COM5, COM8, etc.)
        com_port = find_serial_port()
        if com_port:
            print(f"[GATEWAY] Attempting connection to Serial Port {com_port} (115200 baud)...", flush=True)
            try:
                ser = serial.Serial(com_port, 115200, timeout=1.0)
                print(f"[GATEWAY] CONNECTED to {com_port}! Streaming telemetry...", flush=True)
                LATEST_TELEMETRY["connected"] = True
                LATEST_TELEMETRY["source"] = f"Serial Port ({com_port})"

                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        parse_telemetry_line(line)
            except Exception as e:
                print(f"[GATEWAY] Serial connection on {com_port}: {e}. Retrying...", flush=True)
                LATEST_TELEMETRY["connected"] = False

        time.sleep(1.0)

async def ws_handler(websocket):
    """Handle incoming WebSocket connections from Three.js."""
    CONNECTED_CLIENTS.add(websocket)
    print(f"[WS] Client connected from {websocket.remote_address}", flush=True)
    try:
        while True:
            payload = json.dumps(LATEST_TELEMETRY)
            await websocket.send(payload)
            await asyncio.sleep(0.02)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print("[WS] Client disconnected", flush=True)

async def main():
    if is_port_in_use(8765):
        print("[GATEWAY] WebSocket port 8765 already open. Reusing running service.", flush=True)
        return

    # Start telemetry reader thread
    t = threading.Thread(target=telemetry_worker, daemon=True)
    t.start()

    print("[GATEWAY] Starting WebSocket Server on ws://127.0.0.1:8765 ...", flush=True)
    async with websockets.serve(ws_handler, "127.0.0.1", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[GATEWAY] Stopped by user.", flush=True)
