import math
from gateway.services.safety import SafetySystem

def test_clamp_within_range():
    safety = SafetySystem()
    assert safety.clamp_servo(90.0, 0) == 90.0
    assert safety.clamp_servo(100.0, 1) == 100.0

def test_clamp_below_min():
    safety = SafetySystem()
    assert safety.clamp_servo(20.0, 0) == 50.0

def test_clamp_above_max():
    safety = SafetySystem()
    assert safety.clamp_servo(160.0, 0) == 130.0

def test_nan_inf_protection():
    safety = SafetySystem()
    assert safety.clamp_servo(float("nan"), 0) == 90.0
    assert safety.clamp_servo(float("inf"), 0) == 90.0
