"""
tests/test_desktop_twin_core.py

Unit test suite for app/twin and app/robotics modules.
"""

import math
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.robotics.robot_config import (
    LEG_LABELS,
    JOINT_NAMES,
    STAND_COXA_DEG,
    STAND_FEMUR_DEG,
    STAND_TIBIA_DEG,
    HexapodDimensions,
)
from app.robotics.forward_kinematics import forward_kinematics_3dof
from app.robotics.inverse_kinematics import inverse_kinematics_3dof
from app.robotics.coordinate_frames import (
    imu_to_body,
    body_to_webots,
    body_to_ursina,
    leg_local_to_body,
    body_to_leg_local,
)
from app.robotics.kinematics import HexapodKinematicsEngine
from app.robotics.gait import TripodGaitGenerator

from app.twin.physical_state import PhysicalHardwareState
from app.twin.simulation_state import SimulationState
from app.twin.health import TwinHealthMonitor
from app.twin.twin_state import DigitalTwinState, OperatingMode
from app.twin.synchronizer import TwinSynchronizer


class TestRobotKinematics(unittest.TestCase):
    def setUp(self):
        self.engine = HexapodKinematicsEngine()

    def test_standing_pose_fk(self):
        """Verify standing pose FK puts foot below coxa pivot (negative Z)."""
        x, y, z = self.engine.solve_leg_fk(STAND_COXA_DEG, STAND_FEMUR_DEG, STAND_TIBIA_DEG)
        self.assertGreater(x, 0.05, "Foot should reach outward in X")
        self.assertAlmostEqual(y, 0.0, places=4, msg="Foot should be aligned with Coxa in Y")
        self.assertLess(z, 0.0, "Foot should be below coxa pivot in Z (touching ground)")

    def test_ik_roundtrip(self):
        """Verify IK recovers joint angles from reachable FK foot position."""
        # Test an arbitrary reachable joint configuration
        c_in, f_in, t_in = 10.0, 30.0, -60.0
        x, y, z = self.engine.solve_leg_fk(c_in, f_in, t_in)

        angles = self.engine.solve_leg_ik(x, y, z)
        self.assertIsNotNone(angles, "Target should be within mechanical workspace")
        c_out, f_out, t_out = angles
        self.assertAlmostEqual(c_in, c_out, places=1)
        self.assertAlmostEqual(f_in, f_out, places=1)
        self.assertAlmostEqual(t_in, t_out, places=1)

    def test_ik_unreachable_boundary(self):
        """Verify IK returns None for coordinates exceeding physical leg reach."""
        # 1.0 meter away is far beyond leg length (~0.252m max reach)
        self.assertIsNone(self.engine.solve_leg_ik(1.0, 0.0, 0.0))
        # Negative reach
        self.assertIsNone(self.engine.solve_leg_ik(-0.5, 0.0, 0.0))

    def test_coordinate_frames(self):
        """Verify coordinate transforms."""
        p, r, y = imu_to_body(12.5, -4.2, 33.0)
        self.assertEqual((p, r, y), (12.5, -4.2, 33.0))

        wr, wp, wy = body_to_webots(p, r, y)
        self.assertEqual(wp, -12.5)  # Pitch inverted in Webots

        # Local to body and back roundtrip
        lx, ly, lz = 0.15, 0.0, -0.09
        bx, by, bz = leg_local_to_body("LF", lx, ly, lz)
        rx, ry, rz = body_to_leg_local("LF", bx, by, bz)
        self.assertAlmostEqual(lx, rx, places=4)
        self.assertAlmostEqual(ly, ry, places=4)
        self.assertAlmostEqual(lz, rz, places=4)


class TestTwinSynchronizer(unittest.TestCase):
    def setUp(self):
        self.sync = TwinSynchronizer()

    def test_initial_state(self):
        state = self.sync.get_state()
        self.assertEqual(state.mode, OperatingMode.SIMULATION)
        self.assertFalse(state.emergency_stop)
        self.assertEqual(len(state.target_joint_angles), 18)
        self.assertEqual(len(state.foot_positions_body_frame), 6)

    def test_mirror_18_mapping(self):
        """Verify Mirror-18 distributes physical servo angle across all 18 virtual joints."""
        self.sync.set_operating_mode(OperatingMode.MIRROR_18)
        telemetry = {
            "imu": {"ax": 0.1, "ay": -0.2, "az": 9.8, "gx": 0.0, "gy": 0.0, "gz": 0.0},
            "orientation": {"pitch": 5.0, "roll": -2.0, "yaw": 0.0},
            "servo": {"physical": 110},  # 20 deg offset from 90 center
        }
        self.sync.ingest_hardware_telemetry(telemetry)
        state = self.sync.get_state()

        self.assertEqual(state.physical.servo.measured_angle_deg, 110)
        # Femur should tilt outward (+10 deg from neutral 24 deg)
        self.assertEqual(state.target_joint_angles["lf_femur"], 34.0)
        # Tibia should counter-rotate (-16 deg from neutral -68 deg)
        self.assertEqual(state.target_joint_angles["lf_tibia"], -84.0)

    def test_emergency_stop_latch(self):
        """Verify E-STOP overrides all targets to neutral stance and latches."""
        self.sync.trigger_emergency_stop()
        state = self.sync.get_state()
        self.assertTrue(state.emergency_stop)
        self.assertEqual(state.target_joint_angles["lf_femur"], STAND_FEMUR_DEG)
        self.assertEqual(state.target_joint_angles["lf_tibia"], STAND_TIBIA_DEG)

        self.sync.reset_emergency_stop()
        self.assertFalse(self.sync.get_state().emergency_stop)

    def test_health_evaluation(self):
        """Verify tracking error calculation."""
        # Emulate simulated Webots state with small 1.5 deg discrepancy
        sim_data = {
            "simulationTime": 1.25,
            "rtf": 0.98,
            "orientation": {"pitch": 5.2, "roll": -2.1, "yaw": 0.0},
            "jointPositions": [0.0, 32.5, -82.5] * 6,
            "footContacts": {"lf_foot": True, "lm_foot": True, "lr_foot": True,
                             "rf_foot": True, "rm_foot": True, "rr_foot": True},
        }
        self.sync.ingest_simulation_state(sim_data)
        health = self.sync.get_state().health
        self.assertGreater(health.max_servo_error_deg, 0.0)
        self.assertEqual(health.simulation_rtf, 0.98)


class TestGaitGenerator(unittest.TestCase):
    def test_gait_cycle(self):
        engine = HexapodKinematicsEngine()
        gait = TripodGaitGenerator(engine)
        targets_0 = gait.update(dt=0.1, walk_velocity_m_s=0.03)
        self.assertEqual(len(targets_0), 6)
        for leg, angles in targets_0.items():
            self.assertEqual(len(angles), 3)


if __name__ == "__main__":
    unittest.main()

