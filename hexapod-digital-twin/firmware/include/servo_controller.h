#pragma once
// =============================================================================
// servo_controller.h — Safe servo abstraction with hard angle limits,
//                      emergency-stop latch, and angle tracking
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include <ESP32Servo.h>

class ServoController {
public:
    ServoController();

    /**
     * @brief Attach servo to SERVO_PIN and move to centre position.
     *        Must be called in setup() after Wire.begin().
     */
    void begin();

    /**
     * @brief Command a new angle, clamped to [SERVO_MIN, SERVO_MAX].
     *        Silently ignored when emergency-stopped.
     * @param angle  Desired angle in degrees.
     */
    void setAngle(int angle);

    /** @brief Drive servo to SERVO_CENTER and allow future commands. */
    void center();

    /** @return Last angle written to the servo (degrees). */
    int getCurrentAngle() const;

    /** @return Last angle requested via setAngle() (before clamping). */
    int getCommandAngle() const;

    /**
     * @brief Latch emergency stop: centres servo immediately and rejects
     *        all subsequent setAngle() calls until resetEmergencyStop().
     */
    void emergencyStop();

    /** @brief Release the emergency-stop latch. */
    void resetEmergencyStop();

    /** @return True if the emergency-stop latch is active. */
    bool isEmergencyStopped() const;

private:
    Servo m_servo;
    int   m_currentAngle;    ///< Angle last written to hardware
    int   m_commandAngle;    ///< Raw angle last requested (pre-clamp)
    bool  m_emergencyStopped;

    /**
     * @brief Clamp value to [SERVO_MIN, SERVO_MAX] and write to hardware.
     * @param angle  Unclamped desired angle.
     */
    void writeAngleSafe(int angle);
};
