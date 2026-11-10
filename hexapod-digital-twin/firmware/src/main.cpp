// =============================================================================
// main.cpp — Non-blocking millis() scheduler: IMU 100 Hz | Control 50 Hz
//             | Telemetry 25 Hz | Debug 2 Hz
// Hexapod Digital Twin — Enhanced ESP32 Firmware
//
// Hardware:
//   ESP32-WROOM-32 / MakerBoard
//   MPU-6050 @ I2C 0x69  (SDA=GPIO21, SCL=GPIO22)
//   MG90S servo           (GPIO25)
//   WiFi + WebSocket gateway
//
// NOTE: The original working code in tp03/src/main.cpp is untouched.
//       This firmware lives exclusively in hexapod-digital-twin/firmware/.
// =============================================================================

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#include "config.h"
#include "imu_processor.h"
#include "servo_controller.h"
#include "telemetry_sender.h"

// =============================================================================
// Module-level objects  (the only permitted global mutable state)
// =============================================================================

static Adafruit_MPU6050  g_mpu;
static ImuProcessor      g_imu;
static ServoController   g_servo;
static TelemetrySender   g_telemetry;

// =============================================================================
// Scheduler timestamps
// =============================================================================

static unsigned long g_lastImuMs       = 0;
static unsigned long g_lastControlMs   = 0;
static unsigned long g_lastTelemetryMs = 0;
static unsigned long g_lastDebugMs     = 0;
static unsigned long g_lastWifiMs      = 0;

// =============================================================================
// Application state
// =============================================================================

static bool g_stabilizationEnabled = true;

// Current operating mode label (sent in every telemetry frame)
static const char* g_mode = "MIRROR_18";

// Last sensor events (refreshed on every IMU tick)
static sensors_event_t g_accelEvent;
static sensors_event_t g_gyroEvent;
static sensors_event_t g_tempEvent;   // unused but required by getEvent() API

// =============================================================================
// Forward declarations — command callbacks bound to telemetry command handler
// =============================================================================

static void onCalibrateImu();
static void onResetYaw();
static void onCenterServo();
static void onEnableStabilization();
static void onDisableStabilization();
static void onEmergencyStop();
static void onResetEmergencyStop();

// =============================================================================
// WiFi helpers
// =============================================================================

/**
 * @brief Blocking WiFi connect — called once in setup().
 *        Retries indefinitely with a 500 ms pause between attempts.
 */
static void wifiConnect() {
    Serial.printf("[WiFi] Connecting to SSID '%s'", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print('.');
    }

    Serial.printf("\n[WiFi] Connected. IP: %s\n",
                  WiFi.localIP().toString().c_str());
}

/**
 * @brief Non-blocking WiFi reconnect check — called from the main loop.
 *        Waits WIFI_RECONNECT_MS between attempts to avoid hammering.
 */
static void wifiCheckReconnect() {
    if (WiFi.status() == WL_CONNECTED) {
        return;
    }

    const unsigned long now = millis();
    if (now - g_lastWifiMs >= WIFI_RECONNECT_MS) {
        g_lastWifiMs = now;
        Serial.println(F("[WiFi] Disconnected — attempting reconnect..."));
        WiFi.disconnect();
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
}

// =============================================================================
// MPU-6050 initialisation
// =============================================================================

/**
 * @brief Initialise MPU-6050 over I²C.
 *        On failure: logs error and spins in a retry loop every 2 s.
 */
static void initMpu() {
    Wire.begin(I2C_SDA, I2C_SCL);

    Serial.printf("[IMU] Initialising MPU-6050 at I2C 0x%02X...\n",
                  IMU_I2C_ADDR);

    while (!g_mpu.begin(IMU_I2C_ADDR)) {
        Serial.println(F("[IMU] ERROR: MPU-6050 not found! "
                         "Check wiring (SDA=21, SCL=22, AD0→3.3 V). "
                         "Retrying in 2 s..."));
        delay(2000);
    }

    // Set sensor ranges appropriate for a slow-moving hexapod
    g_mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    g_mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    g_mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

    Serial.println(F("[IMU] MPU-6050 ready."));
}

// =============================================================================
// setup()
// =============================================================================

void setup() {
    Serial.begin(115200);
    delay(200);   // Let serial settle

    Serial.println(F("\n========== Hexapod Digital Twin — ESP32 Firmware =========="));

    // 1. IMU hardware
    initMpu();

    // 2. Servo hardware
    g_servo.begin();

    // 3. Calibrate IMU (blocking — intentional, only at startup)
    g_imu.calibrate(g_mpu, CALIBRATION_SAMPLES);

    // 4. WiFi
    wifiConnect();

    // 5. Register command callbacks with the telemetry sender
    CommandHandlers handlers;
    handlers.onCalibrateImu          = onCalibrateImu;
    handlers.onResetYaw              = onResetYaw;
    handlers.onCenterServo           = onCenterServo;
    handlers.onEnableStabilization   = onEnableStabilization;
    handlers.onDisableStabilization  = onDisableStabilization;
    handlers.onEmergencyStop         = onEmergencyStop;
    handlers.onResetEmergencyStop    = onResetEmergencyStop;
    g_telemetry.setCommandHandlers(handlers);

    // 6. WebSocket
    g_telemetry.begin();

    // Seed scheduler timestamps to stagger first ticks
    const unsigned long now = millis();
    g_lastImuMs       = now;
    g_lastControlMs   = now;
    g_lastTelemetryMs = now;
    g_lastDebugMs     = now;
    g_lastWifiMs      = now;

    Serial.println(F("[MAIN] Setup complete — entering scheduler loop.\n"));
}

// =============================================================================
// loop() — Non-blocking millis() scheduler
// =============================================================================

void loop() {
    const unsigned long now = millis();

    // ------------------------------------------------------------------
    // TICK 1 — IMU read + complementary filter  (100 Hz = every 10 ms)
    // ------------------------------------------------------------------
    if (now - g_lastImuMs >= IMU_PERIOD_MS) {
        const float dt = static_cast<float>(now - g_lastImuMs) / 1000.0f;
        g_lastImuMs = now;

        g_mpu.getEvent(&g_accelEvent, &g_gyroEvent, &g_tempEvent);
        g_imu.update(g_accelEvent, g_gyroEvent, dt);
    }

    // ------------------------------------------------------------------
    // TICK 2 — Servo control (50 Hz = every 20 ms)
    // ------------------------------------------------------------------
    if (now - g_lastControlMs >= CONTROL_PERIOD_MS) {
        g_lastControlMs = now;

        if (g_stabilizationEnabled && !g_servo.isEmergencyStopped()) {
            const FilteredState state = g_imu.getState();

            // Pitch-compensation: rotate servo opposite to body tilt.
            // SERVO_DIRECTION (-1) inverts so servo corrects the lean.
            const float compensation =
                static_cast<float>(SERVO_DIRECTION) * SERVO_GAIN * state.pitch;

            const int targetAngle =
                SERVO_CENTER + static_cast<int>(compensation);

            g_servo.setAngle(targetAngle);
        }
    }

    // ------------------------------------------------------------------
    // TICK 3 — Telemetry transmit (25 Hz = every 40 ms)
    // ------------------------------------------------------------------
    if (now - g_lastTelemetryMs >= TELEMETRY_PERIOD_MS) {
        g_lastTelemetryMs = now;

        g_telemetry.sendTelemetry(g_imu.getState(),
                                   g_accelEvent,
                                   g_gyroEvent,
                                   g_servo.getCurrentAngle(),
                                   g_mode);
    }

    // ------------------------------------------------------------------
    // Continuous — process incoming WebSocket commands (every loop)
    // ------------------------------------------------------------------
    g_telemetry.processIncoming();

    // ------------------------------------------------------------------
    // Continuous — reconnect WiFi / WebSocket if dropped
    // ------------------------------------------------------------------
    wifiCheckReconnect();
    g_telemetry.checkReconnect();

    // ------------------------------------------------------------------
    // DEBUG — Serial status print (2 Hz = every 500 ms)
    // ------------------------------------------------------------------
    if (now - g_lastDebugMs >= DEBUG_PERIOD_MS) {
        g_lastDebugMs = now;

        const FilteredState state = g_imu.getState();
        Serial.printf(
            "[DBG] P=%.2f  R=%.2f  Y=%.2f(drift)  "
            "Servo=%d°  E-Stop=%s  WiFi=%s  WS=%s\n",
            state.pitch, state.roll, state.yaw,
            g_servo.getCurrentAngle(),
            g_servo.isEmergencyStopped() ? "YES" : "no",
            WiFi.status() == WL_CONNECTED   ? "OK"  : "DOWN",
            g_telemetry.isConnected()       ? "OK"  : "DOWN");
    }
}

// =============================================================================
// Command callbacks
// =============================================================================

/** Triggered by CALIBRATE_IMU command from gateway. */
static void onCalibrateImu() {
    Serial.println(F("[CMD] CALIBRATE_IMU — re-running calibration..."));
    // Note: calibrate() is blocking; the scheduler pauses briefly.
    g_imu.calibrate(g_mpu, CALIBRATION_SAMPLES);
}

/** Triggered by RESET_YAW command from gateway. */
static void onResetYaw() {
    Serial.println(F("[CMD] RESET_YAW"));
    g_imu.resetYaw();
}

/** Triggered by CENTER_SERVO command from gateway. */
static void onCenterServo() {
    Serial.println(F("[CMD] CENTER_SERVO"));
    g_servo.center();
}

/** Triggered by ENABLE_STABILIZATION command from gateway. */
static void onEnableStabilization() {
    Serial.println(F("[CMD] ENABLE_STABILIZATION"));
    g_stabilizationEnabled = true;
}

/** Triggered by DISABLE_STABILIZATION command from gateway. */
static void onDisableStabilization() {
    Serial.println(F("[CMD] DISABLE_STABILIZATION — servo will hold last angle."));
    g_stabilizationEnabled = false;
}

/** Triggered by EMERGENCY_STOP command from gateway. */
static void onEmergencyStop() {
    Serial.println(F("[CMD] EMERGENCY_STOP"));
    g_servo.emergencyStop();
    g_stabilizationEnabled = false;
}

/** Triggered by RESET_EMERGENCY_STOP command from gateway. */
static void onResetEmergencyStop() {
    Serial.println(F("[CMD] RESET_EMERGENCY_STOP"));
    g_servo.resetEmergencyStop();
    // Stabilization must be explicitly re-enabled via ENABLE_STABILIZATION
}
