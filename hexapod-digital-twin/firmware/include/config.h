#pragma once
// =============================================================================
// config.h — Centralised compile-time configuration
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

// ---------------------------------------------------------------------------
// WiFi credentials  (replace with your network details)
// ---------------------------------------------------------------------------
#define WIFI_SSID       "YOUR_SSID"
#define WIFI_PASSWORD   "YOUR_PASSWORD"

// ---------------------------------------------------------------------------
// WebSocket gateway
// ---------------------------------------------------------------------------
#define GATEWAY_HOST    "192.168.1.100"
#define GATEWAY_PORT    8765

// ---------------------------------------------------------------------------
// Hardware pin assignments
// ---------------------------------------------------------------------------
#define SERVO_PIN       25          // MG90S servo signal (GPIO25)
#define I2C_SDA         21          // MPU-6050 SDA
#define I2C_SCL         22          // MPU-6050 SCL
#define IMU_I2C_ADDR    0x69        // MPU-6050 AD0 pulled HIGH

// ---------------------------------------------------------------------------
// Servo limits & tuning
// ---------------------------------------------------------------------------
#define SERVO_CENTER    90          // Neutral position (degrees)
#define SERVO_MIN       50          // Hard lower limit (degrees)
#define SERVO_MAX       130         // Hard upper limit (degrees)
#define SERVO_GAIN      1.0f        // Compensation gain scalar
#define SERVO_DIRECTION (-1)        // -1 inverts pitch compensation

// ---------------------------------------------------------------------------
// Complementary filter
// ---------------------------------------------------------------------------
#define ALPHA_COMPLEMENTARY  0.98f  // Gyro weight; (1-ALPHA) = accel weight

// ---------------------------------------------------------------------------
// Task scheduler rates
// ---------------------------------------------------------------------------
#define IMU_RATE_HZ         100     // IMU read + filter update rate
#define CONTROL_RATE_HZ      50     // Servo command rate
#define TELEMETRY_RATE_HZ    25     // WebSocket telemetry rate

// Derived periods in milliseconds
#define IMU_PERIOD_MS       (1000 / IMU_RATE_HZ)
#define CONTROL_PERIOD_MS   (1000 / CONTROL_RATE_HZ)
#define TELEMETRY_PERIOD_MS (1000 / TELEMETRY_RATE_HZ)

// Serial debug print period (2 Hz)
#define DEBUG_PERIOD_MS     500

// ---------------------------------------------------------------------------
// Calibration
// ---------------------------------------------------------------------------
#define CALIBRATION_SAMPLES  200    // Samples averaged during startup cal

// ---------------------------------------------------------------------------
// Reconnect intervals
// ---------------------------------------------------------------------------
#define WIFI_RECONNECT_MS      5000   // Retry WiFi every 5 s
#define WS_RECONNECT_MS        3000   // Retry WebSocket every 3 s
