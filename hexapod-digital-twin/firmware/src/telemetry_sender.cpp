// =============================================================================
// telemetry_sender.cpp — WebSocket JSON telemetry + command dispatcher
// Hexapod Digital Twin — Enhanced ESP32 Firmware
// =============================================================================

#include "telemetry_sender.h"
#include "config.h"

#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------

TelemetrySender::TelemetrySender()
    : m_handlers{nullptr, nullptr, nullptr, nullptr,
                 nullptr, nullptr, nullptr},
      m_lastReconnectAttempt(0),
      m_connected(false)
{}

// ---------------------------------------------------------------------------
// Public methods
// ---------------------------------------------------------------------------

void TelemetrySender::setCommandHandlers(const CommandHandlers& handlers) {
    m_handlers = handlers;
}

void TelemetrySender::begin() {
    // Register the internal message callback once
    m_ws.onMessage([this](websockets::WebsocketsMessage msg) {
        this->dispatchCommand(msg.data());
    });

    m_ws.onEvent([this](websockets::WebsocketsEvent event, String data) {
        if (event == websockets::WebsocketsEvent::ConnectionClosed) {
            m_connected = false;
            Serial.println(F("[WS] Connection closed."));
        }
    });

    connectToGateway();
}

void TelemetrySender::sendTelemetry(const FilteredState&   state,
                                     const sensors_event_t& accel,
                                     const sensors_event_t& gyro,
                                     int                    servoAngle,
                                     const char*            mode) {
    if (!m_connected) {
        return;   // Silently drop; reconnect logic is in checkReconnect()
    }

    // Use a static document to avoid repeated heap allocation at 25 Hz
    // Size calculated for this exact schema + some headroom.
    StaticJsonDocument<384> doc;

    doc["type"]      = "telemetry";
    doc["timestamp"] = millis();

    JsonObject imu = doc.createNestedObject("imu");
    imu["ax"] = accel.acceleration.x;
    imu["ay"] = accel.acceleration.y;
    imu["az"] = accel.acceleration.z;
    imu["gx"] = gyro.gyro.x;
    imu["gy"] = gyro.gyro.y;
    imu["gz"] = gyro.gyro.z;

    JsonObject orientation = doc.createNestedObject("orientation");
    orientation["pitch"]    = state.pitch;
    orientation["roll"]     = state.roll;
    orientation["yaw"]      = state.yaw;
    orientation["yawValid"] = state.yawValid;  // always false (gyro drift)

    JsonObject servo = doc.createNestedObject("servo");
    servo["physical"] = servoAngle;

    doc["mode"] = mode;

    // Serialise to a stack buffer — avoids String heap fragmentation
    char buf[384];
    const size_t len = serializeJson(doc, buf, sizeof(buf));

    if (!m_ws.send(buf, len)) {
        Serial.println(F("[WS] Send failed — marking disconnected."));
        m_connected = false;
    }
}

void TelemetrySender::processIncoming() {
    if (m_connected) {
        m_ws.poll();   // Non-blocking; triggers onMessage callback if data ready
    }
}

void TelemetrySender::checkReconnect() {
    if (m_connected) {
        return;
    }

    const unsigned long now = millis();
    if (now - m_lastReconnectAttempt >= WS_RECONNECT_MS) {
        m_lastReconnectAttempt = now;
        Serial.println(F("[WS] Attempting reconnection..."));
        connectToGateway();
    }
}

bool TelemetrySender::isConnected() const {
    return m_connected;
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

bool TelemetrySender::connectToGateway() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println(F("[WS] WiFi not ready — skipping connect."));
        m_connected = false;
        return false;
    }

    // Build ws://HOST:PORT/
    String url = String("ws://") + GATEWAY_HOST + ":" + GATEWAY_PORT + "/";
    Serial.printf("[WS] Connecting to %s\n", url.c_str());

    m_connected = m_ws.connect(url);

    if (m_connected) {
        Serial.println(F("[WS] Connected to gateway."));
    } else {
        Serial.println(F("[WS] Connection failed."));
    }
    return m_connected;
}

void TelemetrySender::dispatchCommand(const String& payload) {
    Serial.printf("[WS] RX: %s\n", payload.c_str());

    StaticJsonDocument<128> doc;
    const DeserializationError err = deserializeJson(doc, payload);

    if (err) {
        Serial.printf("[WS] JSON parse error: %s\n", err.c_str());
        return;
    }

    if (!doc.containsKey("command")) {
        Serial.println(F("[WS] No 'command' field in message."));
        return;
    }

    const String cmd = doc["command"].as<String>();

    if (cmd == "CALIBRATE_IMU") {
        if (m_handlers.onCalibrateImu) m_handlers.onCalibrateImu();
    } else if (cmd == "RESET_YAW") {
        if (m_handlers.onResetYaw) m_handlers.onResetYaw();
    } else if (cmd == "CENTER_SERVO") {
        if (m_handlers.onCenterServo) m_handlers.onCenterServo();
    } else if (cmd == "ENABLE_STABILIZATION") {
        if (m_handlers.onEnableStabilization) m_handlers.onEnableStabilization();
    } else if (cmd == "DISABLE_STABILIZATION") {
        if (m_handlers.onDisableStabilization) m_handlers.onDisableStabilization();
    } else if (cmd == "EMERGENCY_STOP") {
        if (m_handlers.onEmergencyStop) m_handlers.onEmergencyStop();
    } else if (cmd == "RESET_EMERGENCY_STOP") {
        if (m_handlers.onResetEmergencyStop) m_handlers.onResetEmergencyStop();
    } else {
        Serial.printf("[WS] Unknown command: %s\n", cmd.c_str());
    }
}
