import serial
import time

try:
    ser = serial.Serial('COM8', 115200, timeout=2)
    print("SUCCESS: Opened COM8 successfully!")
    time.sleep(0.5)
    for _ in range(10):
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(f"ESP32_OUTPUT: {line}")
    ser.close()
except Exception as e:
    print(f"ERROR: {e}")

