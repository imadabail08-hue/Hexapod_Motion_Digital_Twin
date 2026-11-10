// =============================================================================
// imu_processor.cpp — IMU calibration, complementary filter, pitch/roll/yaw
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include "imu_processor.h"
#include "config.h"

#include <Arduino.h>
#include <math.h>

// ---------------------------------------------------------------------------
// Free functions
// ---------------------------------------------------------------------------

float calculatePitch(float ax, float ay, float az) {
    // atan2 gives a quadrant-aware result; negate so nose-up is positive.
    return -atan2f(ax, sqrtf(ay * ay + az * az)) * RAD_TO_DEG;
}

float calculateRoll(float ax, float ay, float az) {
    // Roll: rotation about X axis.
    return atan2f(ay, az) * RAD_TO_DEG;
}

// ---------------------------------------------------------------------------
// ImuProcessor
// ---------------------------------------------------------------------------

ImuProcessor::ImuProcessor()
    : m_cal{0.0f, 0.0f, 0.0f, 0.0f, 0.0f},
      m_state{0.0f, 0.0f, 0.0f, false},
      m_calibrated(false)
{}

// ---- calibrate() -----------------------------------------------------------

void ImuProcessor::calibrate(Adafruit_MPU6050& mpu, int samples) {
    Serial.println(F("[IMU] Starting calibration — keep hexapod still..."));

    double sumPitch  = 0.0;
    double sumRoll   = 0.0;
    double sumGx     = 0.0;
    double sumGy     = 0.0;
    double sumGz     = 0.0;

    sensors_event_t accel, gyro, temp;

    for (int i = 0; i < samples; ++i) {
        mpu.getEvent(&accel, &gyro, &temp);

        sumPitch += static_cast<double>(
            calculatePitch(accel.acceleration.x,
                           accel.acceleration.y,
                           accel.acceleration.z));

        sumRoll += static_cast<double>(
            calculateRoll(accel.acceleration.x,
                          accel.acceleration.y,
                          accel.acceleration.z));

        sumGx += static_cast<double>(gyro.gyro.x);
        sumGy += static_cast<double>(gyro.gyro.y);
        sumGz += static_cast<double>(gyro.gyro.z);

        delay(5);   // ~200 Hz during calibration only — blocking is intentional
    }

    const float n = static_cast<float>(samples);
    m_cal.pitchZero  = static_cast<float>(sumPitch / n);
    m_cal.rollZero   = static_cast<float>(sumRoll  / n);
    m_cal.gyroBiasX  = static_cast<float>(sumGx    / n);
    m_cal.gyroBiasY  = static_cast<float>(sumGy    / n);
    m_cal.gyroBiasZ  = static_cast<float>(sumGz    / n);

    // Initialise filter state to the zero offsets
    m_state.pitch    = 0.0f;
    m_state.roll     = 0.0f;
    m_state.yaw      = 0.0f;
    m_state.yawValid = false;  // Gyro-only yaw always drifts

    m_calibrated = true;

    Serial.printf(F("[IMU] Calibration done. pitchZero=%.2f  rollZero=%.2f  "
                    "gyroBiasX=%.4f  gyroBiasY=%.4f  gyroBiasZ=%.4f\n"),
                  m_cal.pitchZero, m_cal.rollZero,
                  m_cal.gyroBiasX, m_cal.gyroBiasY, m_cal.gyroBiasZ);
}

// ---- update() --------------------------------------------------------------

void ImuProcessor::update(const sensors_event_t& accel,
                           const sensors_event_t& gyro,
                           float dt) {
    if (!m_calibrated) {
        // Silently ignore until calibration is complete.
        return;
    }

    // -- Bias-corrected gyro rates (rad/s) --
    const float gx = gyro.gyro.x - m_cal.gyroBiasX;
    const float gy = gyro.gyro.y - m_cal.gyroBiasY;
    const float gz = gyro.gyro.z - m_cal.gyroBiasZ;

    // -- Accelerometer-derived angles (absolute reference) --
    const float accelPitch = calculatePitch(accel.acceleration.x,
                                             accel.acceleration.y,
                                             accel.acceleration.z)
                             - m_cal.pitchZero;

    const float accelRoll  = calculateRoll(accel.acceleration.x,
                                            accel.acceleration.y,
                                            accel.acceleration.z)
                             - m_cal.rollZero;

    // -- Complementary filter: fuse gyro prediction with accel correction --
    // Gyro integration uses Y-axis rate for pitch, X-axis rate for roll.
    m_state.pitch = ALPHA_COMPLEMENTARY * (m_state.pitch + gy * dt * RAD_TO_DEG)
                  + (1.0f - ALPHA_COMPLEMENTARY) * accelPitch;

    m_state.roll  = ALPHA_COMPLEMENTARY * (m_state.roll  + gx * dt * RAD_TO_DEG)
                  + (1.0f - ALPHA_COMPLEMENTARY) * accelRoll;

    // -- Gyro-integrated yaw (no magnetometer → drift is unavoidable) --
    m_state.yaw     += gz * dt * RAD_TO_DEG;
    m_state.yawValid = false;   // Warn caller: yaw accumulates drift
}

// ---- Accessors -------------------------------------------------------------

FilteredState ImuProcessor::getState() const {
    return m_state;
}

void ImuProcessor::resetYaw() {
    m_state.yaw      = 0.0f;
    m_state.yawValid = false;
    Serial.println(F("[IMU] Yaw reset to 0."));
}

CalibrationData ImuProcessor::getCalibration() const {
    return m_cal;
}

bool ImuProcessor::isCalibrated() const {
    return m_calibrated;
}
