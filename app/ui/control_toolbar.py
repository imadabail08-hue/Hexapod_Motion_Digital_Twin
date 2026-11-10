"""
app/ui/control_toolbar.py

Top System Status Header and Bottom Engineering Action Bar.
Provides direct command dispatching, status indicators, and industrial E-STOP latching.
"""

from __future__ import annotations

from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QCheckBox
)
from PySide6.QtCore import Qt

from app.twin.twin_state import DigitalTwinState, OperatingMode


class TopStatusHeader(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(14)

        # Title / Identifier
        lbl_id = QLabel("HEX-01")
        lbl_id.setStyleSheet("font-size: 16px; font-weight: 900; color: #00bcd4; letter-spacing: 1px;")

        lbl_sub = QLabel("HEXAPOD MOTION DIGITAL TWIN  |  ESP32 • MPU6050 • 18 DOF")
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: bold; color: #8c8c96;")

        layout.addWidget(lbl_id)
        layout.addWidget(lbl_sub)
        layout.addStretch()

        # Status Indicators
        self.badge_esp = QLabel("ESP32: OFFLINE")
        self.badge_esp.setObjectName("badgeErr")

        self.badge_webots = QLabel("WEBOTS: STANDBY")
        self.badge_webots.setObjectName("badgeWarn")

        self.badge_sync = QLabel("SYNC: LOST")
        self.badge_sync.setObjectName("badgeErr")

        self.badge_mode = QLabel("MODE: SIMULATION")
        self.badge_mode.setObjectName("badgeMode")

        self.lbl_telemetry = QLabel("50.0 Hz  |  12 ms  |  60 FPS")
        self.lbl_telemetry.setObjectName("numReadoutMuted")

        layout.addWidget(self.badge_esp)
        layout.addWidget(self.badge_webots)
        layout.addWidget(self.badge_sync)
        layout.addWidget(self.badge_mode)
        layout.addWidget(self.lbl_telemetry)

    def update_header(self, state: DigitalTwinState, fps: int = 60):
        # ESP32
        if state.physical.esp32_connected:
            self.badge_esp.setText("ESP32: CONNECTED")
            self.badge_esp.setObjectName("badgeOk")
        else:
            self.badge_esp.setText("ESP32: OFFLINE")
            self.badge_esp.setObjectName("badgeErr")
        self.badge_esp.setStyle(self.badge_esp.style())

        # Webots
        if state.simulation.webots_running:
            self.badge_webots.setText(f"WEBOTS: RUNNING ({state.simulation.real_time_factor:.2f}x)")
            self.badge_webots.setObjectName("badgeOk")
        else:
            self.badge_webots.setText("WEBOTS: STANDBY")
            self.badge_webots.setObjectName("badgeWarn")
        self.badge_webots.setStyle(self.badge_webots.style())

        # Sync
        sync = state.health.sync_status
        self.badge_sync.setText(f"SYNC: {sync}")
        if sync == "GOOD":
            self.badge_sync.setObjectName("badgeOk")
        elif sync == "DEGRADED":
            self.badge_sync.setObjectName("badgeWarn")
        else:
            self.badge_sync.setObjectName("badgeErr")
        self.badge_sync.setStyle(self.badge_sync.style())

        # Mode
        self.badge_mode.setText(f"MODE: {state.mode.value}")
        self.lbl_telemetry.setText(f"{state.health.telemetry_hz:.1f} Hz  |  {state.health.latency_ms:.0f} ms  |  {fps} FPS")


class BottomActionBar(QFrame):
    def __init__(
        self,
        on_calibrate: Callable[[], None],
        on_center: Callable[[], None],
        on_toggle_mirror: Callable[[], None],
        on_toggle_sim: Callable[[], None],
        on_toggle_record: Callable[[], None],
        on_estop: Callable[[], None],
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("bottomBar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.btn_calib = QPushButton("CALIBRATE IMU")
        self.btn_calib.clicked.connect(on_calibrate)

        self.btn_center = QPushButton("CENTER SERVO")
        self.btn_center.clicked.connect(on_center)

        self.btn_mirror = QPushButton("MIRROR 18 MODE")
        self.btn_mirror.clicked.connect(on_toggle_mirror)

        self.btn_sim = QPushButton("SIMULATION MODE")
        self.btn_sim.clicked.connect(on_toggle_sim)

        self.btn_record = QPushButton("● START RECORDING")
        self.btn_record.clicked.connect(on_toggle_record)

        self.hw_gate = QCheckBox("HARDWARE COMMAND GATE")
        self.hw_gate.setStyleSheet("color: #ff9800; font-size: 11px; font-weight: bold;")

        layout.addWidget(self.btn_calib)
        layout.addWidget(self.btn_center)
        layout.addWidget(self.btn_mirror)
        layout.addWidget(self.btn_sim)
        layout.addWidget(self.btn_record)
        layout.addWidget(self.hw_gate)
        layout.addStretch()

        # E-STOP button
        self.btn_estop = QPushButton("🛑 EMERGENCY STOP")
        self.btn_estop.setObjectName("btnEstop")
        self.btn_estop.clicked.connect(on_estop)
        layout.addWidget(self.btn_estop)

    def set_estop_state(self, active: bool):
        if active:
            self.btn_estop.setText("⚠ RESET EMERGENCY STOP")
            self.btn_estop.setObjectName("btnEstopReset")
        else:
            self.btn_estop.setText("🛑 EMERGENCY STOP")
            self.btn_estop.setObjectName("btnEstop")
        self.btn_estop.setStyle(self.btn_estop.style())
