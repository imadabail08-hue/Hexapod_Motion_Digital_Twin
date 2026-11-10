"""
app/ui/actuator_panel.py

Right dockable panel displaying:
- Physical Actuator status (MG90S on GPIO 25, safe envelope [50°-130°])
- 18 Actuated Joint States grouped by leg (Target, Actual, Discrepancy Error)
"""

from __future__ import annotations

from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QScrollArea, QProgressBar, QFrame
)
from PySide6.QtCore import Qt

from app.robotics.robot_config import LEG_LABELS, JOINT_NAMES


class JointRowWidget(QFrame):
    def __init__(self, joint_name: str, parent=None):
        super().__init__(parent)
        self.joint_name = joint_name
        self.setFixedHeight(24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(6)

        # Segment label (e.g., COXA, FEMUR, TIBIA)
        seg = joint_name.split("_")[1].upper()
        self.lbl_name = QLabel(seg)
        self.lbl_name.setFixedWidth(46)
        self.lbl_name.setStyleSheet("font-size: 10px; color: #8c8c96; font-weight: bold;")

        # Progress bar representing angle
        self.bar = QProgressBar()
        self.bar.setRange(-90, 90)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)

        # Target & Error labels
        self.lbl_target = QLabel("0.0°")
        self.lbl_target.setFixedWidth(42)
        self.lbl_target.setObjectName("numReadoutMuted")

        self.lbl_err = QLabel("±0.0°")
        self.lbl_err.setFixedWidth(40)
        self.lbl_err.setStyleSheet("font-family: monospace; font-size: 10px; color: #81c784;")

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.bar)
        layout.addWidget(self.lbl_target)
        layout.addWidget(self.lbl_err)

    def set_values(self, target: float, actual: float):
        err = abs(target - actual)
        self.bar.setValue(int(target))
        self.lbl_target.setText(f"{target:+.1f}°")
        self.lbl_err.setText(f"±{err:.1f}°")

        # Color based on error
        if err > 3.0:
            self.lbl_err.setStyleSheet("font-family: monospace; font-size: 10px; color: #ef9a9a; font-weight: bold;")
        elif err > 1.5:
            self.lbl_err.setStyleSheet("font-family: monospace; font-size: 10px; color: #ffb74d;")
        else:
            self.lbl_err.setStyleSheet("font-family: monospace; font-size: 10px; color: #81c784;")


class ActuatorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # 1. Physical MG90S Card
        grp_phys = QGroupBox("PHYSICAL ACTUATOR (PROOF-OF-CONCEPT)")
        l_phys = QVBoxLayout(grp_phys)
        l_phys.setSpacing(4)

        self.lbl_phys_servo = QLabel("MG90S SERVO  |  GPIO 25\nTARGET: 90°   STATE: 90°")
        self.lbl_phys_servo.setObjectName("numReadoutValue")
        lbl_safe = QLabel("HARDWARE ENVELOPE: SAFE [50° – 130°]")
        lbl_safe.setStyleSheet("color: #00bcd4; font-size: 10px; font-weight: bold;")

        l_phys.addWidget(self.lbl_phys_servo)
        l_phys.addWidget(lbl_safe)
        layout.addWidget(grp_phys)

        # 2. 18 Joint Telemetry Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        container = QWidget()
        l_cont = QVBoxLayout(container)
        l_cont.setContentsMargins(0, 0, 0, 0)
        l_cont.setSpacing(6)

        self.joint_rows: Dict[str, JointRowWidget] = {}

        for leg in LEG_LABELS:
            grp_leg = QGroupBox(f"{leg} LEG ACTUATORS")
            l_leg = QVBoxLayout(grp_leg)
            l_leg.setContentsMargins(4, 8, 4, 4)
            l_leg.setSpacing(2)

            prefix = leg.lower()
            for seg in ["coxa", "femur", "tibia"]:
                name = f"{prefix}_{seg}"
                row = JointRowWidget(name)
                self.joint_rows[name] = row
                l_leg.addWidget(row)

            l_cont.addWidget(grp_leg)

        l_cont.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def update_actuator_state(self, targets: Dict[str, float], actuals: Dict[str, float], phys_angle: int):
        self.lbl_phys_servo.setText(f"MG90S SERVO  |  GPIO 25\nTARGET: {phys_angle}°   MEASURED: {phys_angle}°")
        for name, row in self.joint_rows.items():
            t = targets.get(name, 0.0)
            a = actuals.get(name, 0.0)
            row.set_values(t, a)
