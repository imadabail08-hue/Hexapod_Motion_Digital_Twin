# ⬡ INDUSTRIAL HEXAPOD REAL-TIME DIGITAL TWIN PLATFORM

An industrial-grade cyber-physical digital twin architecture synchronizing **ESP32 Hardware**, **MPU6050 6-Axis IMU**, **Physical Servomotors**, **Webots Physics Simulation**, **Three.js / React Three Fiber HMI**, **Ursina 3D Engineering Viewer**, and **Pygame Diagnostics Console**.

---

## 1. System Architecture

```
                    PHYSICAL LAYER
                          │
                  ┌───────▼────────┐
                  │    MPU6050     │  Address: 0x69
                  │ Accel + Gyro   │  SDA: GPIO21, SCL: GPIO22
                  └───────┬────────┘
                          │ I2C (400 kHz)
                          ▼
                  ┌────────────────┐
                  │     ESP32      │  MakerBoard WROOM-32
                  │  Embedded Core │  Non-blocking 100Hz/50Hz/25Hz
                  └───────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │ PWM (50 Hz)
              │                       ▼
              │                  MG90S Servo (GPIO25)
              │                  Physical POC Actuator
              │
              ▼ WebSocket JSON (25–50 Hz)
    ┌───────────────────────────────────┐
    │     PYTHON DIGITAL TWIN GATEWAY   │  FastAPI + AsyncIO
    │         (Port 8765 / 8080)        │  Central State Authority
    └─────────────────┬─────────────────┘
                      │
       ┌──────────────┼──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  WEBOTS  │  │ THREE.JS │   │  URSINA  │   │  PYGAME  │
  │ Physics  │  │ Web HMI  │   │ 3D Debug │   │ Console  │
  │ Twin     │  │ (R3F)    │   │ Viewer   │   │ Diagnos. │
  └──────────┘  └──────────┘   └──────────┘   └──────────┘
```

---

## 2. Six-Layer State Separation Philosophy

The platform strictly separates telemetry and control into 6 authoritative software concepts:

1. **RAW SENSOR STATE**: Directly ingested raw readings ($a_x, a_y, a_z, g_x, g_y, g_z$) from MPU6050.
2. **FILTERED STATE**: Noise-filtered attitude (Pitch, Roll, integrated Yaw) produced via complementary filter ($\alpha = 0.98$).
3. **CONTROL STATE**: Operating mode machine, authority arbitrator, and joint command vectors.
4. **PHYSICAL STATE**: Actual physical hardware state from the ESP32 (MG90S angle clamped to safe envelope $[50^\circ, 130^\circ]$).
5. **SIMULATED STATE**: Multi-body physics state from Webots (ODE simulated joint angles, touch sensors, RTF).
6. **DIGITAL TWIN STATE**: Authoritative merged snapshot broadcast to all client dashboards.

---

## 3. Physical Prototype vs Full 18-DOF Hexapod

| Feature | Current Physical Prototype | Complete Digital Twin Model |
|---|---|---|
| **Legs** | 1 Reference Actuator (POC) | 6 Articulated Legs (LF, RF, LM, RM, LR, RR) |
| **Joints** | 1 Positional Servo (MG90S on GPIO25) | 18 Virtual Servos (Coxa, Femur, Tibia $\times$ 6) |
| **IMU** | MPU6050 (0x69) on GPIO21/GPIO22 | Fused 6-DOF / 9-DOF Attitude with Drift Warning |
| **Modes** | **MIRROR 18 MODE** & **LIVE HARDWARE** | **FULL 18 SERVO**, **SIMULATION**, **MANUAL**, **REPLAY** |

### Mirror-18 Mode Kinematic Mapping
In Prototype Mirror Mode, the single physical servo angle $S$ drives all 18 virtual joints with proper kinematics:
$$\theta_{\text{joint}, i} = \text{direction}_i \times (S - 90^\circ) + 90^\circ + \text{offset}_i$$
Clamped strictly to mechanical safety limits $[50^\circ, 130^\circ]$.

---

## 4. Hardware Wiring & Pinout

| Subsystem | Signal / Pin | ESP32 GPIO | Description |
|---|---|---|---|
| **MPU6050 IMU** | SDA | **GPIO 21** | I2C Data (detected at `0x69`) |
| **MPU6050 IMU** | SCL | **GPIO 22** | I2C Clock |
| **MPU6050 IMU** | VCC / GND | 3.3V / GND | Power supply |
| **MG90S Servo** | PWM Signal | **GPIO 25** | Positional Servo (50 Hz, $500\text{--}2400\,\mu\text{s}$) |
| **MG90S Servo** | Power | 5V / GND | External power recommended |

---

## 5. Directory Structure

```
hexapod-digital-twin/
├── firmware/                 # Non-blocking ESP32 firmware (PlatformIO / Arduino)
│   ├── platformio.ini
│   ├── include/config.h      # Pinout, WiFi credentials, safe limits
│   └── src/main.cpp          # 100Hz IMU / 50Hz Control / 25Hz Telemetry scheduler
│
├── gateway/                  # Python FastAPI & WebSocket Gateway
│   ├── main.py               # Central coordinator
│   ├── config/settings.py
│   ├── models/twin_state.py  # Pydantic v2 authoritative models
│   └── services/             # Twin state, safety supervisor, recorder, Webots bridge
│
├── webots/                   # Webots Robotics Physics Simulation
│   ├── worlds/hexapod.wbt    # 18-joint multi-body physics world
│   ├── protos/HexapodLeg.proto
│   └── controllers/twin_controller/
│
├── threejs-dashboard/        # React + TypeScript + React Three Fiber Industrial HMI
│   ├── src/App.tsx
│   ├── src/robot/HexapodModel.tsx
│   └── src/components/       # StatusHeader, OrientationPanel, Recharts graphs
│
├── ursina-viewer/            # Secondary Python 3D Engineering Viewer
│   └── main.py
│
├── pygame-diagnostics/       # Terminal-style desktop telemetry console
│   └── main.py
│
└── shared/                   # Common protocols, kinematics, robot parameters, unit tests
    ├── protocol/servo_map.py
    ├── config/robot_params.yaml
    └── tests/
```

---

## 6. How to Run the Complete Platform

### Terminal 1: Python Gateway (Central Middleware)
```bash
cd hexapod-digital-twin/gateway
pip install -r requirements.txt
python main.py
```
*Listens on: HTTP `:8000`, Visualizer WebSocket `:8080`, ESP32 WebSocket `:8765`, Webots TCP `:8766`.*

### Terminal 2: Three.js Web HMI Workstation
```bash
cd hexapod-digital-twin/threejs-dashboard
npm install
npm run dev
```
*Open `http://localhost:5173` in your browser.*

### Terminal 3: Webots Simulation Engine
```bash
webots hexapod-digital-twin/webots/worlds/hexapod.wbt
```

### Terminal 4 (Optional): Ursina 3D Engineering Viewer
```bash
python hexapod-digital-twin/ursina-viewer/main.py
```

### Terminal 5 (Optional): Pygame Diagnostics Console
```bash
pip install -r hexapod-digital-twin/pygame-diagnostics/requirements.txt
python hexapod-digital-twin/pygame-diagnostics/main.py
```

---

## 7. Safety System & E-STOP
The platform includes an industrial software safety watchdog:
- **Emergency Stop (E-STOP)**: Immediate return to neutral pose ($90^\circ$), latching lock on hardware commands. Requires explicit manual reset.
- **Hardware Command Gate**: In MANUAL mode, commands to physical hardware are locked unless `HARDWARE COMMAND ENABLE` is explicitly engaged.
- **Watchdog Supervisor**: Triggers automatic safe fallback if packet communication times out ($>5.0\,\text{s}$).
- **NaN / Infinity Protection**: Rejects corrupted float values from uncalibrated sensor reads.

---

## 8. Verification & Acceptance Checklist

- [x] **ESP32 Firmware**: Non-blocking `millis()` architecture, complementary filter with Roll/Pitch, drift warning on Yaw, safety bounds clamped.
- [x] **Gateway**: Multi-client WebSocket broadcast at 40 Hz, Pydantic validation, recording export to CSV/JSON.
- [x] **Webots**: 6 articulated legs with 18 RotationalMotors and TouchSensors on feet.
- [x] **Three.js**: Industrial SCADA theme, smooth SLERP body orientation, 18 articulated joint bars, rolling Recharts graphs.
- [x] **Ursina**: Frame transform matrices, coordinate debugging.
- [x] **Pygame**: Desktop dashboard with attitude history, status indicators, and industrial buttons.
- [x] **Unit Tests**: Full coverage for kinematics, frame transformations, servo limits, telemetry validation, and state machine.
