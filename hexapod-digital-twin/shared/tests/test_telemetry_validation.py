from gateway.services.safety import SafetySystem

def test_valid_telemetry():
    safety = SafetySystem()
    valid_pkt = {
        "type": "telemetry",
        "imu": {"ax": 0.1, "ay": 0.2, "az": 9.8, "gx": 0.0, "gy": 0.0, "gz": 0.0},
    }
    assert safety.validate_telemetry(valid_pkt) is True

def test_missing_keys():
    safety = SafetySystem()
    pkt = {"type": "telemetry", "imu": {"ax": 0.1}}
    assert safety.validate_telemetry(pkt) is False

def test_nan_values():
    safety = SafetySystem()
    pkt = {
        "type": "telemetry",
        "imu": {"ax": float("nan"), "ay": 0.2, "az": 9.8, "gx": 0.0, "gy": 0.0, "gz": 0.0},
    }
    assert safety.validate_telemetry(pkt) is False

def test_extreme_values():
    safety = SafetySystem()
    pkt = {
        "type": "telemetry",
        "imu": {"ax": 500.0, "ay": 0.2, "az": 9.8, "gx": 0.0, "gy": 0.0, "gz": 0.0},
    }
    assert safety.validate_telemetry(pkt) is False
