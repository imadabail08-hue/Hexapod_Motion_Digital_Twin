#pragma once
// =============================================================================
// telemetry_sender.h — WebSocket telemetry publisher and command receiver
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include <ArduinoWebsockets.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include "imu_processor.h"   // FilteredState

// Forward-declare to avoid circular includes; main.cpp binds the callbacks.
class ServoController;
class ImuProcessor;

// ---------------------------------------------------------------------------
// Command callback function pointer types
// ---------------------------------------------------------------------------
using CmdCallback = void (*)();          ///< Zero-argument command handler

/**
 * @brief Bundles all external command callbacks so TelemetrySender does not
 *        need direct references to the other subsystems.
 */
struct CommandHandlers {
    CmdCallback onCalibrateImu;           ///< CALIBRATE_IMU
    CmdCallback onResetYaw;               ///< RESET_YAW
    CmdCallback onCenterServo;            ///< CENTER_SERVO
    CmdCallback onEnableStabilization;    ///< ENABLE_STABILIZATION
    CmdCallback onDisableStabilization;   ///< DISABLE_STABILIZATION
    CmdCallback onEmergencyStop;          ///< EMERGENCY_STOP
    CmdCallback onResetEmergencyStop;     ///< RESET_EMERGENCY_STOP
};

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

class TelemetrySender {
public:
    TelemetrySender();

    /**
     * @brief Register command callbacks (call before begin()).
     * @param handlers  Struct of function pointers for each command type.
     */
    void setCommandHandlers(const CommandHandlers& handlers);

    /**
     * @brief Attempt to connect to the WebSocket gateway.
     *        Non-blocking after first connect attempt; reconnects are handled
     *        by checkReconnect() called from the main loop.
     */
    void begin();

    /**
     * @brief Build and transmit a JSON telemetry frame over WebSocket.
     *
     * JSON schema:
     * {
     *   "type": "telemetry",
     *   "timestamp": <millis>,
     *   "imu": { "ax":…, "ay":…, "az":…, "gx":…, "gy":…, "gz":… },
     *   "orientation": { "pitch":…, "roll":…, "yaw":…, "yawValid": false },
     *   "servo": { "physical": <angle> },
     *   "mode": "<modeStr>"
     * }
     *
     * @param state       Fused orientation from ImuProcessor.
     * @param accel       Raw accelerometer event.
     * @param gyro        Raw gyroscope event.
     * @param servoAngle  Current physical servo angle (degrees).
     * @param mode        Operating mode string, e.g. "MIRROR_18".
     */
    void sendTelemetry(const FilteredState&    state,
                       const sensors_event_t&  accel,
                       const sensors_event_t&  gyro,
                       int                     servoAngle,
                       const char*             mode);

    /**
     * @brief Poll the WebSocket library for incoming messages and dispatch
     *        to the appropriate command callback.  Call every loop iteration.
     */
    void processIncoming();

    /**
     * @brief Attempt reconnection if the socket is down.
     *        Respects WS_RECONNECT_MS to avoid hammering the gateway.
     */
    void checkReconnect();

    /** @return True if the WebSocket connection is currently open. */
    bool isConnected() const;

private:
    websockets::WebsocketsClient m_ws;
    CommandHandlers              m_handlers;
    unsigned long                m_lastReconnectAttempt;
    bool                         m_connected;

    /** @brief Internal connect helper (blocks only for the TCP handshake). */
    bool connectToGateway();

    /** @brief Dispatch a received JSON command string to the right callback. */
    void dispatchCommand(const String& payload);
};
