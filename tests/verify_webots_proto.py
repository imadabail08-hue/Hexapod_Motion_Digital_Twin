with open('webots/protos/HexapodDigitalTwin.proto', 'r', encoding='utf-8') as f:
    content = f.read()

joints = [
    'lf_coxa', 'lf_femur', 'lf_tibia',
    'lm_coxa', 'lm_femur', 'lm_tibia',
    'lr_coxa', 'lr_femur', 'lr_tibia',
    'rf_coxa', 'rf_femur', 'rf_tibia',
    'rm_coxa', 'rm_femur', 'rm_tibia',
    'rr_coxa', 'rr_femur', 'rr_tibia'
]

print(f"Checking {len(joints)} joints in PROTO...")
for j in joints:
    assert f'name "{j}"' in content, f"Missing motor: {j}"
    assert f'name "{j}_sensor"' in content, f"Missing sensor: {j}_sensor"

feet = ['lf_foot', 'lm_foot', 'lr_foot', 'rf_foot', 'rm_foot', 'rr_foot']
for ft in feet:
    assert f'name "{ft}"' in content, f"Missing foot sensor: {ft}"

assert 'name "imu"' in content
assert 'name "gyro"' in content
assert 'name "accelerometer"' in content

print("SUCCESS: All 18 motors, 18 sensors, 6 foot contact sensors, and 3 IMU units verified in Webots PROTO!")
