from ursina_viewer.robot.frame_transforms import (
    imu_to_robot,
    robot_to_webots,
    robot_to_threejs,
    imu_to_ursina,
)

def test_imu_to_robot():
    p, r, y = imu_to_robot(10.0, -5.0, 30.0)
    assert p == 10.0
    assert r == -5.0
    assert y == 30.0

def test_robot_to_webots():
    r, p, y = robot_to_webots(15.0, 10.0, 45.0)
    assert p == -15.0
    assert r == 10.0
    assert y == 45.0

def test_robot_to_threejs():
    x, y, z = robot_to_threejs(20.0, 10.0, 0.0)
    assert x == -10.0
    assert z == -20.0
