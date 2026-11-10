"""
app/ui/robot_3d_viewport.py

Real-Time 3D OpenGL Engineering Viewport for HEX-01 Hexapod.
Uses pyqtgraph.opengl (GLViewWidget) for high-performance native desktop rendering.
Renders chassis plates, 6 standoffs, electronics, and 6 articulated 3-DOF legs with proper kinematic pivots.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Dict, Tuple, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt

import pyqtgraph.opengl as gl

from app.robotics.robot_config import (
    LEG_LABELS,
    LEG_MOUNT_ANGLES_DEG,
    get_leg_mount_position,
    DEFAULT_BODY_RADIUS,
    DEFAULT_COXA_LEN,
    DEFAULT_FEMUR_LEN,
    DEFAULT_TIBIA_LEN,
    STAND_COXA_DEG,
    STAND_FEMUR_DEG,
    STAND_TIBIA_DEG,
)


class Robot3DViewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Camera toolbar
        self.cam_toolbar = QFrame()
        self.cam_toolbar.setFixedHeight(34)
        self.cam_toolbar.setStyleSheet("background-color: #1a1a1e; border-bottom: 1px solid #2e2e34;")
        cam_layout = QHBoxLayout(self.cam_toolbar)
        cam_layout.setContentsMargins(8, 2, 8, 2)
        cam_layout.setSpacing(6)

        title = QLabel("3D KINEMATIC VIEWPORT")
        title.setStyleSheet("color: #00bcd4; font-weight: bold; font-size: 11px;")
        cam_layout.addWidget(title)
        cam_layout.addStretch()

        presets = [
            ("ISO", self.set_cam_iso),
            ("TOP", self.set_cam_top),
            ("FRONT", self.set_cam_front),
            ("RIGHT", self.set_cam_right),
            ("RESET", self.set_cam_iso),
        ]
        for name, callback in presets:
            btn = QPushButton(name)
            btn.setFixedHeight(24)
            btn.setStyleSheet("padding: 2px 8px; font-size: 10px;")
            btn.clicked.connect(callback)
            cam_layout.addWidget(btn)

        layout.addWidget(self.cam_toolbar)

        # 2. OpenGL View Widget
        self.gl_view = gl.GLViewWidget()
        self.gl_view.setBackgroundColor("#141416")
        layout.addWidget(self.gl_view)

        # 3. Floor Grid & World Axes
        grid = gl.GLGridItem()
        grid.setSize(x=1.2, y=1.2, z=0)
        grid.setSpacing(x=0.05, y=0.05, z=0)
        grid.translate(0, 0, -0.095)  # Position at ground level
        grid.setColor((50, 50, 60, 160))
        self.gl_view.addItem(grid)

        axis = gl.GLAxisItem()
        axis.setSize(x=0.1, y=0.1, z=0.1)
        axis.translate(0, 0, -0.095)
        self.gl_view.addItem(axis)

        # 4. Robot Visual Items Storage
        self.leg_lines: Dict[str, gl.GLLinePlotItem] = {}
        self.foot_points: Dict[str, gl.GLScatterPlotItem] = {}

        self._build_chassis_geometry()
        self._build_leg_visuals()

        # Initial camera pose
        self.set_cam_iso()

    def set_cam_iso(self):
        self.gl_view.setCameraPosition(distance=0.65, elevation=28, azimuth=45)

    def set_cam_top(self):
        self.gl_view.setCameraPosition(distance=0.60, elevation=89, azimuth=0)

    def set_cam_front(self):
        self.gl_view.setCameraPosition(distance=0.60, elevation=5, azimuth=0)

    def set_cam_right(self):
        self.gl_view.setCameraPosition(distance=0.60, elevation=5, azimuth=90)

    def _build_chassis_geometry(self):
        # Hexagonal upper plate outline
        angles = np.linspace(0, 2 * np.pi, 7)
        r = DEFAULT_BODY_RADIUS
        pts_upper = np.array([[r * math.cos(a), r * math.sin(a), 0.018] for a in angles])
        pts_lower = np.array([[r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), -0.018] for a in angles])

        self.chassis_upper_line = gl.GLLinePlotItem(pos=pts_upper, color=(0.7, 0.7, 0.75, 1.0), width=2.5, mode='line_strip')
        self.chassis_lower_line = gl.GLLinePlotItem(pos=pts_lower, color=(0.4, 0.4, 0.45, 1.0), width=2.0, mode='line_strip')
        self.gl_view.addItem(self.chassis_upper_line)
        self.gl_view.addItem(self.chassis_lower_line)

        # Central PCB Electronics box outline
        pcb_box = np.array([
            [-0.025, -0.015, 0.022], [0.025, -0.015, 0.022],
            [0.025, 0.015, 0.022], [-0.025, 0.015, 0.022],
            [-0.025, -0.015, 0.022]
        ])
        self.pcb_outline = gl.GLLinePlotItem(pos=pcb_box, color=(0.1, 0.8, 0.5, 1.0), width=2.0, mode='line_strip')
        self.gl_view.addItem(self.pcb_outline)

    def _build_leg_visuals(self):
        for leg in LEG_LABELS:
            # 4 kinematic points: coxa pivot -> femur pivot -> knee pivot -> foot contact
            pts = np.zeros((4, 3))
            line = gl.GLLinePlotItem(pos=pts, color=(0.95, 0.45, 0.1, 1.0), width=3.5, mode='line_strip')
            self.gl_view.addItem(line)
            self.leg_lines[leg] = line

            # Foot sphere marker
            foot_pt = gl.GLScatterPlotItem(pos=np.array([[0, 0, 0]]), color=(0.1, 0.1, 0.1, 1.0), size=12)
            self.gl_view.addItem(foot_pt)
            self.foot_points[leg] = foot_pt

    def update_robot_pose(
        self,
        joint_angles: Dict[str, float],
        pitch_deg: float = 0.0,
        roll_deg: float = 0.0,
        yaw_deg: float = 0.0,
        foot_contacts: Optional[Dict[str, bool]] = None,
    ):
        """Update 3D robot articulation based on joint angles and body attitude."""
        # Convert body rotation to rotation matrix
        pr = math.radians(pitch_deg)
        rr = math.radians(roll_deg)
        yr = math.radians(yaw_deg)

        # R = Rz(yaw) * Ry(pitch) * Rx(roll)
        cy, sy = math.cos(yr), math.sin(yr)
        cp, sp = math.cos(pr), math.sin(pr)
        cr, sr = math.cos(rr), math.sin(rr)

        R = np.array([
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp,     cp * sr,                cp * cr]
        ])

        # Update chassis lines
        angles = np.linspace(0, 2 * np.pi, 7)
        r = DEFAULT_BODY_RADIUS
        pts_u = np.array([[r * math.cos(a), r * math.sin(a), 0.018] for a in angles])
        pts_l = np.array([[r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), -0.018] for a in angles])
        self.chassis_upper_line.setData(pos=np.dot(pts_u, R.T))
        self.chassis_lower_line.setData(pos=np.dot(pts_l, R.T))

        # Update each of the 6 legs
        for leg in LEG_LABELS:
            mount_ang_deg = LEG_MOUNT_ANGLES_DEG.get(leg, 0.0)
            prefix = leg.lower()

            c_deg = joint_angles.get(f"{prefix}_coxa", STAND_COXA_DEG)
            f_deg = joint_angles.get(f"{prefix}_femur", STAND_FEMUR_DEG)
            t_deg = joint_angles.get(f"{prefix}_tibia", STAND_TIBIA_DEG)

            # Leg Mount coordinate in body frame
            ang_rad = math.radians(mount_ang_deg)
            p0 = np.array([DEFAULT_BODY_RADIUS * math.cos(ang_rad), DEFAULT_BODY_RADIUS * math.sin(ang_rad), 0.0])

            # Kinematic link vectors in leg local frame
            c_rad = math.radians(mount_ang_deg + c_deg)
            f_rad = math.radians(f_deg)
            t_rad = math.radians(t_deg)

            # Coxa vector (horizontal)
            v_coxa = np.array([DEFAULT_COXA_LEN * math.cos(c_rad), DEFAULT_COXA_LEN * math.sin(c_rad), 0.0])
            p1 = p0 + v_coxa

            # Femur vector (elevated)
            v_femur = np.array([
                DEFAULT_FEMUR_LEN * math.cos(f_rad) * math.cos(c_rad),
                DEFAULT_FEMUR_LEN * math.cos(f_rad) * math.sin(c_rad),
                DEFAULT_FEMUR_LEN * math.sin(f_rad)
            ])
            p2 = p1 + v_femur

            # Tibia vector
            knee_rad = f_rad + t_rad
            v_tibia = np.array([
                DEFAULT_TIBIA_LEN * math.cos(knee_rad) * math.cos(c_rad),
                DEFAULT_TIBIA_LEN * math.cos(knee_rad) * math.sin(c_rad),
                DEFAULT_TIBIA_LEN * math.sin(knee_rad)
            ])
            p3 = p2 + v_tibia

            # Rotate all points by body attitude R
            leg_pts = np.array([p0, p1, p2, p3])
            rot_pts = np.dot(leg_pts, R.T)

            self.leg_lines[leg].setData(pos=rot_pts)

            # Color foot sphere: green if contact, dark if airborne
            in_contact = foot_contacts.get(f"{prefix}_foot", True) if foot_contacts else True
            foot_col = (0.3, 0.85, 0.3, 1.0) if in_contact else (0.9, 0.6, 0.1, 1.0)
            self.foot_points[leg].setData(pos=np.array([rot_pts[3]]), color=foot_col)
