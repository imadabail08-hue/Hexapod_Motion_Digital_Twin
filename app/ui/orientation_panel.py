"""
app/ui/orientation_panel.py

Left dockable panel displaying:
- Measured Body Orientation (Pitch, Roll, Yaw) with drift warning
- Raw 6-axis IMU readouts (Accelerometer, Gyroscope)
- Artificial Horizon instrumentation
- Calibration state
"""

from __future__ import annotations

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from app.twin.physical_state import PhysicalHardwareState


class ArtificialHorizonWidget(QFrame):
    """Circular flight-instrument style attitude indicator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self.pitch_deg = 0.0
        self.roll_deg = 0.0

    def set_attitude(self, pitch: float, roll: float):
        self.pitch_deg = pitch
        self.roll_deg = roll
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 4

        # Background circular dial
        painter.setBrush(QBrush(QColor("#18181c")))
        painter.setPen(QPen(QColor("#2e2e34"), 2))
        painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.roll_deg)  # Roll rotation

        # Pitch displacement (clamped to dial)
        pitch_px = max(-r + 10, min(r - 10, int(self.pitch_deg * 1.5)))

        # Horizon line
        painter.setPen(QPen(QColor("#00bcd4"), 2))
        painter.drawLine(-r + 8, pitch_px, r - 8, pitch_px)

        # Pitch scale marks
        painter.setPen(QPen(QColor("#80deea"), 1))
        painter.drawLine(-20, pitch_px - 20, 20, pitch_px - 20)
        painter.drawLine(-20, pitch_px + 20, 20, pitch_px + 20)

        painter.restore()

        # Fixed center reference aircraft symbol (orange)
        painter.setPen(QPen(QColor("#ff9800"), 2))
        painter.drawLine(cx - 24, cy, cx - 8, cy)
        painter.drawLine(cx + 8, cy, cx + 24, cy)
        painter.drawEllipse(cx - 3, cy - 3, 6, 6)


class OrientationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Orientation Group Box
        grp_orient = QGroupBox("BODY ATTITUDE & FUSION")
        l_orient = QVBoxLayout(grp_orient)
        l_orient.setSpacing(6)

        # Horizon in center
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        self.horizon = ArtificialHorizonWidget()
        h_layout.addWidget(self.horizon)
        h_layout.addStretch()
        l_orient.addLayout(h_layout)

        # Numerical readouts
        self.lbl_pitch = QLabel("PITCH:  +0.0°")
        self.lbl_pitch.setObjectName("numReadoutValue")
        self.lbl_roll  = QLabel("ROLL:   +0.0°")
        self.lbl_roll.setObjectName("numReadoutValue")
        self.lbl_yaw   = QLabel("YAW:    +0.0°")
        self.lbl_yaw.setObjectName("numReadoutValue")

        self.lbl_yaw_warn = QLabel("GYRO-INTEGRATED / DRIFT EXPECTED")
        self.lbl_yaw_warn.setStyleSheet("color: #ff9800; font-size: 9px; font-weight: bold;")

        l_orient.addWidget(self.lbl_pitch)
        l_orient.addWidget(self.lbl_roll)
        l_orient.addWidget(self.lbl_yaw)
        l_orient.addWidget(self.lbl_yaw_warn)
        layout.addWidget(grp_orient)

        # 2. Raw IMU Group Box
        grp_imu = QGroupBox("MPU6050 SENSOR TELEMETRY")
        l_imu = QVBoxLayout(grp_imu)
        l_imu.setSpacing(4)

        self.lbl_accel = QLabel("ACCEL (m/s²):\nX: +0.00  Y: +0.00  Z: +9.81")
        self.lbl_accel.setObjectName("numReadoutMuted")
        self.lbl_accel_mag = QLabel("|a| Magnitude: 9.81 m/s²")
        self.lbl_accel_mag.setObjectName("numReadoutMuted")

        self.lbl_gyro = QLabel("GYRO (°/s):\nX: +0.0  Y: +0.0  Z: +0.0")
        self.lbl_gyro.setObjectName("numReadoutMuted")

        self.lbl_calib = QLabel("CALIBRATION: ACTIVE OFFSET SAVED")
        self.lbl_calib.setStyleSheet("color: #81c784; font-size: 10px; font-weight: bold;")

        l_imu.addWidget(self.lbl_accel)
        l_imu.addWidget(self.lbl_accel_mag)
        l_imu.addWidget(self.lbl_gyro)
        l_imu.addWidget(self.lbl_calib)
        layout.addWidget(grp_imu)

        layout.addStretch()

    def update_hardware_state(self, phys: PhysicalHardwareState):
        p = phys.attitude.pitch_deg
        r = phys.attitude.roll_deg
        y = phys.attitude.yaw_deg

        self.horizon.set_attitude(p, r)
        self.lbl_pitch.setText(f"PITCH:  {p:+.1f}°")
        self.lbl_roll.setText(f"ROLL:   {r:+.1f}°")
        self.lbl_yaw.setText(f"YAW:    {y:+.1f}°")

        ax, ay, az = phys.imu.ax, phys.imu.ay, phys.imu.az
        gx, gy, gz = phys.imu.gx, phys.imu.gy, phys.imu.gz
        mag = math.sqrt(ax * ax + ay * ay + az * az)

        self.lbl_accel.setText(f"ACCEL (m/s²):\nX: {ax:+.2f}  Y: {ay:+.2f}  Z: {az:+.2f}")
        self.lbl_accel_mag.setText(f"|a| Magnitude: {mag:.2f} m/s²")
        self.lbl_gyro.setText(f"GYRO (°/s):\nX: {gx:+.1f}  Y: {gy:+.1f}  Z: {gz:+.1f}")
