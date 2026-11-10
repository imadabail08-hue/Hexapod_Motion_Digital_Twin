from gateway.services.safety import SafetySystem
from gateway.services.recorder import TelemetryRecorder
from gateway.services.twin_state_manager import TwinStateManager

def test_mirror18_propagation():
    safety = SafetySystem()
    recorder = TelemetryRecorder()
    mgr = TwinStateManager(safety, recorder)

    mgr.apply_mirror_18(90)
    assert len(mgr.get_state().virtualServos) == 18
    for s in mgr.get_state().virtualServos:
        assert s == 90.0

def test_mirror18_offset_and_clamp():
    safety = SafetySystem()
    recorder = TelemetryRecorder()
    mgr = TwinStateManager(safety, recorder)

    mgr.apply_mirror_18(120)
    # Servos should reflect command clamped to safe envelope
    for s in mgr.get_state().virtualServos:
        assert 50.0 <= s <= 130.0
