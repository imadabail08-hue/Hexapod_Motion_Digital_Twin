// =============================================================================
// servo_controller.cpp — MG90S servo with hard limits and e-stop latch
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include "servo_controller.h"
#include "config.h"

#include <Arduino.h>
#include <algorithm>    // std::clamp (ESP-IDF toolchain provides <algorithm>)

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------

ServoController::ServoController()
    : m_currentAngle(SERVO_CENTER),
      m_commandAngle(SERVO_CENTER),
      m_emergencyStopped(false)
{}

// ---------------------------------------------------------------------------
// Public methods
// ---------------------------------------------------------------------------

void ServoController::begin() {
    // Allow ESP32Servo to use any available timer channel
    m_servo.setPeriodHertz(50);                     // Standard 50 Hz PWM
    m_servo.attach(SERVO_PIN, 500, 2400);           // 500–2400 µs pulse range
    writeAngleSafe(SERVO_CENTER);
    Serial.printf("[SERVO] Attached on GPIO%d — centred at %d°\n",
                  SERVO_PIN, SERVO_CENTER);
}

void ServoController::setAngle(int angle) {
    if (m_emergencyStopped) {
        // All motion commands rejected during e-stop
        return;
    }
    m_commandAngle = angle;
    writeAngleSafe(angle);
}

void ServoController::center() {
    m_commandAngle = SERVO_CENTER;
    writeAngleSafe(SERVO_CENTER);
}

int ServoController::getCurrentAngle() const {
    return m_currentAngle;
}

int ServoController::getCommandAngle() const {
    return m_commandAngle;
}

void ServoController::emergencyStop() {
    m_emergencyStopped = true;
    writeAngleSafe(SERVO_CENTER);   // Safe position immediately
    Serial.println(F("[SERVO] EMERGENCY STOP — servo centred, commands locked."));
}

void ServoController::resetEmergencyStop() {
    m_emergencyStopped = false;
    Serial.println(F("[SERVO] Emergency stop cleared — commands re-enabled."));
}

bool ServoController::isEmergencyStopped() const {
    return m_emergencyStopped;
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

void ServoController::writeAngleSafe(int angle) {
    // Hard clamp: firmware enforces limits regardless of caller
    const int clamped = std::max(SERVO_MIN, std::min(SERVO_MAX, angle));

    if (clamped != angle) {
        Serial.printf("[SERVO] Angle %d° clamped to %d° (limits [%d, %d])\n",
                      angle, clamped, SERVO_MIN, SERVO_MAX);
    }

    m_servo.write(clamped);
    m_currentAngle = clamped;
}
