#pragma once
// =============================================================================
// imu_processor.h — IMU data processing: calibration, complementary filter,
//                   pitch / roll / yaw estimation
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ---------------------------------------------------------------------------
// Free functions — pure geometric calculations (no state)
// ---------------------------------------------------------------------------

/**
 * @brief Compute pitch angle from raw accelerometer values.
 * @param ax  Acceleration on X axis (m/s²)
 * @param ay  Acceleration on Y axis (m/s²)
 * @param az  Acceleration on Z axis (m/s²)
 * @return    Pitch in degrees  [-90, +90]
 */
float calculatePitch(float ax, float ay, float az);

/**
 * @brief Compute roll angle from raw accelerometer values.
 * @param ax  Acceleration on X axis (m/s²)
 * @param ay  Acceleration on Y axis (m/s²)
 * @param az  Acceleration on Z axis (m/s²)
 * @return    Roll in degrees  [-180, +180]
 */
float calculateRoll(float ax, float ay, float az);

// ---------------------------------------------------------------------------
// Data structures
// ---------------------------------------------------------------------------

/**
 * @brief Static offsets measured during the startup calibration routine.
 */
struct CalibrationData {
    float pitchZero;    ///< Accel-derived pitch at rest (degrees)
    float rollZero;     ///< Accel-derived roll at rest (degrees)
    float gyroBiasX;    ///< Gyro X-axis bias (rad/s)
    float gyroBiasY;    ///< Gyro Y-axis bias (rad/s)
    float gyroBiasZ;    ///< Gyro Z-axis bias (rad/s)
};

/**
 * @brief Fused orientation output from the complementary filter.
 */
struct FilteredState {
    float pitch;       ///< Fused pitch (degrees), bias-corrected
    float roll;        ///< Fused roll  (degrees), bias-corrected
    float yaw;         ///< Gyro-integrated yaw (degrees) — drifts over time
    bool  yawValid;    ///< Always false: gyro-only yaw has uncorrected drift
};

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

class ImuProcessor {
public:
    ImuProcessor();

    /**
     * @brief Blocking calibration — call once at startup before the scheduler.
     *        Averages `samples` readings to compute zero offsets and gyro bias.
     * @param mpu      Reference to the initialised Adafruit_MPU6050 object.
     * @param samples  Number of samples to average (see CALIBRATION_SAMPLES).
     */
    void calibrate(Adafruit_MPU6050& mpu, int samples);

    /**
     * @brief Non-blocking filter update — call every IMU tick.
     * @param accel  Accelerometer event from mpu.getEvent().
     * @param gyro   Gyroscope event from mpu.getEvent().
     * @param dt     Time since last call (seconds).
     */
    void update(const sensors_event_t& accel,
                const sensors_event_t& gyro,
                float dt);

    /** @return Current fused orientation (const reference). */
    FilteredState getState() const;

    /** @brief Reset integrated yaw to 0.0 degrees. */
    void resetYaw();

    /** @return A copy of the calibration offsets. */
    CalibrationData getCalibration() const;

    /** @return True if calibration has been completed. */
    bool isCalibrated() const;

private:
    CalibrationData m_cal;
    FilteredState   m_state;
    bool            m_calibrated;
};
