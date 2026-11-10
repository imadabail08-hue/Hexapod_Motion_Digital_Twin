import pytest
from gateway.services.kinematics import LegKinematics, DEFAULT_LEG_DIMS

def test_fk_neutral():
    solver = LegKinematics(DEFAULT_LEG_DIMS)
    x, y, z = solver.forward_kinematics(90.0, 90.0, 90.0)
    assert round(y, 3) == 0.0
    assert x > 0.0

def test_fk_tibia_extension():
    solver = LegKinematics(DEFAULT_LEG_DIMS)
    x_neutral, _, z_neutral = solver.forward_kinematics(90.0, 90.0, 90.0)
    x_ext, _, z_ext = solver.forward_kinematics(90.0, 90.0, 140.0)
    assert x_ext != x_neutral or z_ext != z_neutral

def test_ik_reachable():
    solver = LegKinematics(DEFAULT_LEG_DIMS)
    x, y, z = solver.forward_kinematics(90.0, 90.0, 90.0)
    angles = solver.inverse_kinematics(x, y, z)
    assert angles is not None
    c, f, t = angles
    assert abs(c - 90.0) < 1.0

def test_ik_unreachable():
    solver = LegKinematics(DEFAULT_LEG_DIMS)
    # Beyond max reach (10 metres away)
    angles = solver.inverse_kinematics(10.0, 10.0, 10.0)
    assert angles is None
