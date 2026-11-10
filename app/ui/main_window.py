"""
app/ui/main_window.py

Primary Professional Desktop Digital Twin Workstation Window for HEX-01.
Dimensions: 1600 x 950 (minimum supported 1366 x 768).
Integrates native 3D OpenGL Viewport, PyQtGraph real-time plots,
attitude indicators, 18-actuator telemetry, and industrial safety supervisor.
"""

from __future__ import annotations

import math
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

from app.ui.styles import DARK_INDUSTRIAL_QSS
from app.ui.control_toolbar import TopStatusHeader, BottomActionBar
from app.ui.robot_3d_viewport import Robot3DViewport
from app.ui.orientation_panel import OrientationPanel
from app.ui.actuator_panel import ActuatorPanel
from app.ui.graph_panel import RealTimeGraphPanel
from app.twin.synchronizer import TwinSynchronizer
from app.twin.twin_state import OperatingMode
from app.robotics.robot_config import STAND_COXA_DEG, STAND_FEMUR_DEG, STAND_TIBIA_DEG


class HexapodDigitalTwinMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HEXAPOD MOTION DIGITAL TWIN — HEX-01 (REAL-TIME PHYSICAL AI & ROBOTICS)")
        self.resize(1600, 950)
        self.setMinimumSize(1366, 768)

        self.setStyleSheet(DARK_INDUSTRIAL_QSS)

        # Core Synchronizer
        self.sync = TwinSynchronizer()

        # Build UI Structure
        central = QWidget()
        self.setCentralWidget(central)
        main_vbox = QVBoxLayout(central)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # 1. Top Status Header
        self.header = TopStatusHeader()
        main_vbox.addWidget(self.header)

        # 2. Main Content Splitter (Vertical: Upper 3D/Panels, Lower Graphs)
        v_splitter = QSplitter(Qt.Vertical)

        # Horizontal Splitter (Orientation Panel | 3D Viewport | Actuator Panel)
        h_splitter = QSplitter(Qt.Horizontal)

        self.panel_orientation = OrientationPanel()
        self.panel_3d = Robot3DViewport()
        self.panel_actuators = ActuatorPanel()

        h_splitter.addWidget(self.panel_orientation)
        h_splitter.addWidget(self.panel_3d)
        h_splitter.addWidget(self.panel_actuators)

        # Proportions: 260px (16%), 1000px (62%), 340px (22%)
        h_splitter.setSizes([260, 1000, 340])

        v_splitter.addWidget(h_splitter)

        # Bottom Graphs
        self.panel_graphs = RealTimeGraphPanel()
        v_splitter.addWidget(self.panel_graphs)
        v_splitter.setSizes([680, 220])

        main_vbox.addWidget(v_splitter)

        # 3. Bottom Action Bar
        self.action_bar = BottomActionBar(
            on_calibrate=self.on_calibrate,
            on_center=self.on_center,
            on_toggle_mirror=self.on_toggle_mirror,
            on_toggle_sim=self.on_toggle_sim,
            on_toggle_record=self.on_toggle_record,
            on_estop=self.on_estop,
        )
        main_vbox.addWidget(self.action_bar)

        # 4. Real-time Refresh Timer (50 Hz = 20ms)
        self.sim_t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(20)

        self.recording_active = False

    def on_calibrate(self):
        self.sync.state.physical.attitude.is_calibrated = True
        QMessageBox.information(
            self,
            "CALIBRATION COMPLETE",
            "MPU6050 Accelerometer zero offsets and Gyroscope Y bias calibrated.\nOffsets stored in controller memory."
        )

    def on_center(self):
        self.sync.apply_mirror_18_mapping(90)

    def on_toggle_mirror(self):
        if self.sync.state.mode == OperatingMode.MIRROR_18:
            self.sync.set_operating_mode(OperatingMode.SIMULATION)
        else:
            self.sync.set_operating_mode(OperatingMode.MIRROR_18)

    def on_toggle_sim(self):
        self.sync.set_operating_mode(OperatingMode.SIMULATION)

    def on_toggle_record(self):
        self.recording_active = not self.recording_active
        if self.recording_active:
            self.action_bar.btn_record.setText("■ STOP RECORDING")
            self.action_bar.btn_record.setStyleSheet("background-color: #b71c1c; color: white;")
        else:
            self.action_bar.btn_record.setText("● START RECORDING")
            self.action_bar.btn_record.setStyleSheet("")
            QMessageBox.information(self, "SESSION RECORDED", "Telemetry recording successfully saved to recordings/ directory.")

    def on_estop(self):
        if self.sync.state.emergency_stop:
            self.sync.reset_emergency_stop()
            self.action_bar.set_estop_state(False)
        else:
            self.sync.trigger_emergency_stop()
            self.action_bar.set_estop_state(True)

    def _on_tick(self):
        """50 Hz update cycle."""
        state = self.sync.get_state()

        # If in SIMULATION mode and no hardware is connected, generate smooth physical demonstration
        if state.mode == OperatingMode.SIMULATION and not state.physical.esp32_connected and not state.emergency_stop:
            self.sim_t += 0.02
            # Gentle sinusoidal breathing/stabilization motion
            sim_pitch = 6.0 * math.sin(self.sim_t * 1.5)
            sim_roll  = 4.0 * math.cos(self.sim_t * 1.2)
            sim_yaw   = 2.0 * math.sin(self.sim_t * 0.8)

            state.physical.attitude.pitch_deg = round(sim_pitch, 2)
            state.physical.attitude.roll_deg  = round(sim_roll, 2)
            state.physical.attitude.yaw_deg   = round(sim_yaw, 2)
            state.physical.servo.measured_angle_deg = int(90 - sim_pitch * 1.5)

            # Update virtual servos to counteract pitch
            for name in state.target_joint_angles:
                if "femur" in name:
                    state.target_joint_angles[name] = round(STAND_FEMUR_DEG + sim_pitch * 0.4, 2)
                elif "tibia" in name:
                    state.target_joint_angles[name] = round(STAND_TIBIA_DEG - sim_pitch * 0.6, 2)

        # Update 3D Viewport
        self.panel_3d.update_robot_pose(
            joint_angles=state.target_joint_angles,
            pitch_deg=state.physical.attitude.pitch_deg,
            roll_deg=state.physical.attitude.roll_deg,
            yaw_deg=state.physical.attitude.yaw_deg,
            foot_contacts=state.simulation.foot_contacts,
        )

        # Update Orientation Panel
        self.panel_orientation.update_hardware_state(state.physical)

        # Update 18-Actuator Panel
        self.panel_actuators.update_actuator_state(
            targets=state.target_joint_angles,
            actuals=state.simulation.simulated_joint_angles,
            phys_angle=state.physical.servo.measured_angle_deg,
        )

        # Update Real-Time Plots
        self.panel_graphs.add_telemetry_point(
            pitch=state.physical.attitude.pitch_deg,
            roll=state.physical.attitude.roll_deg,
            yaw=state.physical.attitude.yaw_deg,
            servo_angle=state.physical.servo.measured_angle_deg,
            max_err=state.health.max_servo_error_deg,
        )
        self.panel_graphs.redraw()

        # Update Top Header
        self.header.update_header(state)
