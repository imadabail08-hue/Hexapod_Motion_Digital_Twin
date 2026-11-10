from gateway.models.operating_mode import ModeStateMachine, OperatingMode

def test_initial_mode():
    sm = ModeStateMachine()
    assert sm.current == OperatingMode.SIMULATION

def test_transition_with_hardware():
    sm = ModeStateMachine()
    # Transition to live hardware requires ESP32 connected
    ok = sm.transition(OperatingMode.LIVE_HARDWARE, esp32_connected=False)
    assert ok is False
    assert sm.current == OperatingMode.SIMULATION

    ok2 = sm.transition(OperatingMode.LIVE_HARDWARE, esp32_connected=True)
    assert ok2 is True
    assert sm.current == OperatingMode.LIVE_HARDWARE
