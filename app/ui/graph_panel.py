"""
app/ui/graph_panel.py

High-Performance Desktop Real-Time Engineering Plots using PyQtGraph.
Displays:
- Attitude tracking: Pitch (cyan), Roll (green), Yaw (amber)
- Actuator tracking: MG90S Physical Servo angle
- Digital Twin tracking error
"""

from __future__ import annotations

import collections
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
import pyqtgraph as pg


class RealTimeGraphPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Header bar
        header = QFrame()
        header.setFixedHeight(26)
        l_h = QHBoxLayout(header)
        l_h.setContentsMargins(4, 0, 4, 0)

        t_lbl = QLabel("REAL-TIME ATTITUDE & ACTUATOR TELEMETRY (ROLLING BUFFER)")
        t_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #8c8c96;")
        l_h.addWidget(t_lbl)
        l_h.addStretch()

        l_h.addWidget(QLabel("WINDOW:"))
        self.combo_win = QComboBox()
        self.combo_win.addItems(["10 SECONDS", "20 SECONDS", "60 SECONDS"])
        self.combo_win.setCurrentIndex(1)
        self.combo_win.setFixedHeight(22)
        self.combo_win.currentIndexChanged.connect(self._change_window)
        l_h.addWidget(self.combo_win)

        layout.addWidget(header)

        # PyQtGraph Plot Layout
        pg.setConfigOption('background', '#18181c')
        pg.setConfigOption('foreground', '#8c8c96')
        pg.setConfigOptions(antialias=True)

        self.win = pg.GraphicsLayoutWidget()
        layout.addWidget(self.win)

        # Plot 1: Attitude (Pitch, Roll, Yaw)
        self.p_attitude = self.win.addPlot(title="<span style='color:#00bcd4; font-size:10pt;'>BODY ATTITUDE (°): PITCH (CYAN) / ROLL (GREEN) / YAW (AMBER)</span>")
        self.p_attitude.showGrid(x=True, y=True, alpha=0.3)
        self.p_attitude.setYRange(-45, 45)
        self.p_attitude.setLabel('left', 'Angle (deg)')

        self.curve_pitch = self.p_attitude.plot(pen=pg.mkPen(color='#00bcd4', width=2))
        self.curve_roll  = self.p_attitude.plot(pen=pg.mkPen(color='#4caf50', width=2))
        self.curve_yaw   = self.p_attitude.plot(pen=pg.mkPen(color='#ff9800', width=1, style=pg.QtCore.Qt.DashLine))

        # Plot 2: Physical Servo MG90S & Error
        self.p_servo = self.win.addPlot(title="<span style='color:#ff5722; font-size:10pt;'>PHYSICAL SERVO MG90S (50°–130°) & MAX TWIN ERROR</span>")
        self.p_servo.showGrid(x=True, y=True, alpha=0.3)
        self.p_servo.setYRange(40, 140)
        self.p_servo.setLabel('left', 'Servo Angle (deg)')

        self.curve_servo = self.p_servo.plot(pen=pg.mkPen(color='#ff5722', width=2))
        self.curve_error = self.p_servo.plot(pen=pg.mkPen(color='#ef5350', width=1.5))

        # Circular data buffers (default 20s at 50Hz = 1000 points)
        self.max_pts = 1000
        self.buf_pitch = collections.deque(maxlen=self.max_pts)
        self.buf_roll  = collections.deque(maxlen=self.max_pts)
        self.buf_yaw   = collections.deque(maxlen=self.max_pts)
        self.buf_servo = collections.deque(maxlen=self.max_pts)
        self.buf_err   = collections.deque(maxlen=self.max_pts)

    def _change_window(self, idx: int):
        sizes = [500, 1000, 3000]
        self.max_pts = sizes[idx]
        self.buf_pitch = collections.deque(self.buf_pitch, maxlen=self.max_pts)
        self.buf_roll  = collections.deque(self.buf_roll,  maxlen=self.max_pts)
        self.buf_yaw   = collections.deque(self.buf_yaw,   maxlen=self.max_pts)
        self.buf_servo = collections.deque(self.buf_servo, maxlen=self.max_pts)
        self.buf_err   = collections.deque(self.buf_err,   maxlen=self.max_pts)

    def add_telemetry_point(self, pitch: float, roll: float, yaw: float, servo_angle: float, max_err: float):
        self.buf_pitch.append(pitch)
        self.buf_roll.append(roll)
        self.buf_yaw.append(yaw)
        self.buf_servo.append(servo_angle)
        self.buf_err.append(max_err)

    def redraw(self):
        """Redraw curves efficiently."""
        if len(self.buf_pitch) > 1:
            self.curve_pitch.setData(list(self.buf_pitch))
            self.curve_roll.setData(list(self.buf_roll))
            self.curve_yaw.setData(list(self.buf_yaw))
            self.curve_servo.setData(list(self.buf_servo))
            self.curve_error.setData(list(self.buf_err))
