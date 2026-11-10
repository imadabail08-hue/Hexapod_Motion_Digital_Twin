#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ESP32Servo.h>
#include <math.h>

/* ==============================================================================
   HEXAPOD MOTION DIGITAL TWIN - FIRMWARE INDUSTRIEL ESP32 & WOKWI
   Concept : Commande de Locomotion Hexapode par Inclinaison MPU (Tilt-to-Walk)
   - État initial (à plat) : Robot fixe, corps horizontal, servo à 90°, repos absolu
   - Inclinaison avant (Pitch > 0) : Marche en avant (les pattes marchent)
   - Inclinaison arrière (Pitch < 0) : Marche en arrière
   - Le servo GPIO 19 exécute la foulée de patte synchronisée
   - Protection Wokwi 0g et anti-dérive Yaw intégrée
   ============================================================================== */

Adafruit_MPU6050 mpu;
Servo servoFoot;

const int SERVO_PIN = 19;
bool mpuAvailable = false;
uint8_t mpuAddress = 0x68;

// Constantes Physiques
const float GRAVITY_1G = 9.80665; // m/s²

// Offsets d'Étalonnage IMU
float pitchOffset = 0.0;
float rollOffset  = 0.0;
float gyroBiasX   = 0.0;
float gyroBiasY   = 0.0;
float gyroBiasZ   = 0.0;

// Angles Filtrés (Attitude Réelle du Robot)
float rollFiltered  = 0.0;
float pitchFiltered = 0.0;
float yawEstimated  = 0.0;

// Gestion du Temps & Marche
unsigned long previousMicros = 0;
float walkPhase = 0.0;

// Asservissement Servo Patte
float targetServoAngle  = 90.0;
float currentServoAngle = 90.0;
int   lastWrittenAngle  = 90;

float computePitchAccel(float ax, float ay, float az)
{
    return atan2(-ax, sqrt(ay * ay + az * az)) * RAD_TO_DEG;
}

float computeRollAccel(float ay, float az)
{
    return atan2(ay, az) * RAD_TO_DEG;
}

void setup()
{
    Serial.begin(115200);
    delay(300);

    Wire.begin(21, 22);
    Wire.setClock(400000);

    Serial.println();
    Serial.println("==========================================================");
    Serial.println("  HEXAPOD MOTION LAB — TILT-TO-WALK INERTIAL LOCOMOTION   ");
    Serial.println("  ESP32 · MPU6050 Auto-Detect · Servo Patte MG90S (GPIO 19)");
    Serial.println("==========================================================");

    servoFoot.setPeriodHertz(50);
    servoFoot.attach(SERVO_PIN, 500, 2400);
    servoFoot.write(90);
    currentServoAngle = 90.0;
    targetServoAngle  = 90.0;
    lastWrittenAngle  = 90;
    Serial.println("[+] Servo Patte MG90S initialise sur GPIO 19 (Neutre 90 deg).");

    if (mpu.begin(0x68, &Wire)) {
        mpuAvailable = true;
        mpuAddress = 0x68;
        Serial.println("[+] MPU6050 detecte et initialise a l'adresse 0x68 (Wokwi).");
    } else if (mpu.begin(0x69, &Wire)) {
        mpuAvailable = true;
        mpuAddress = 0x69;
        Serial.println("[+] MPU6050 detecte et initialise a l'adresse 0x69 (Hardware).");
    } else {
        Serial.println("[!] MPU6050 non detecte sur bus I2C.");
        mpuAvailable = false;
    }

    if (mpuAvailable) {
        mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
        mpu.setGyroRange(MPU6050_RANGE_250_DEG);
        mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

        // Calibration rapide si gravité présente
        sensors_event_t a, g, t;
        mpu.getEvent(&a, &g, &t);
        float mag = sqrt(a.acceleration.x * a.acceleration.x +
                         a.acceleration.y * a.acceleration.y +
                         a.acceleration.z * a.acceleration.z);

        if (mag > 4.0) {
            const int SAMPLES = 50;
            float sumP = 0, sumR = 0, sumGz = 0;
            for (int i = 0; i < SAMPLES; i++) {
                mpu.getEvent(&a, &g, &t);
                sumP += computePitchAccel(a.acceleration.x, a.acceleration.y, a.acceleration.z);
                sumR += computeRollAccel(a.acceleration.y, a.acceleration.z);
                sumGz += (g.gyro.z * RAD_TO_DEG);
                delay(5);
            }
            pitchOffset = sumP / SAMPLES;
            rollOffset  = sumR / SAMPLES;
            gyroBiasZ   = sumGz / SAMPLES;
        }
    }

    previousMicros = micros();
    Serial.println("[+] SYSTEME OPERATIONNEL — Neutre 0° actif, en attente de commande MPU.");
    Serial.println("----------------------------------------------------------");
}

void loop()
{
    unsigned long currentMicros = micros();
    float dt = (currentMicros - previousMicros) / 1000000.0;
    if (dt <= 0.0005 || dt > 0.1) dt = 0.02;
    previousMicros = currentMicros;

    if (mpuAvailable) {
        sensors_event_t accel, gyro, temp;
        mpu.getEvent(&accel, &gyro, &temp);

        float accelMag = sqrt(accel.acceleration.x * accel.acceleration.x +
                              accel.acceleration.y * accel.acceleration.y +
                              accel.acceleration.z * accel.acceleration.z);

        // Si Wokwi a des curseurs à 0g (pas de gravité), on reste stable à 0°
        if (accelMag > 2.0) {
            float rawPitch = computePitchAccel(accel.acceleration.x, accel.acceleration.y, accel.acceleration.z) - pitchOffset;
            float rawRoll  = computeRollAccel(accel.acceleration.y, accel.acceleration.z) - rollOffset;

            float gyroRateX = (gyro.gyro.x * RAD_TO_DEG) - gyroBiasX;
            float gyroRateY = (gyro.gyro.y * RAD_TO_DEG) - gyroBiasY;
            float gyroRateZ = (gyro.gyro.z * RAD_TO_DEG) - gyroBiasZ;

            // Filtre complémentaire
            float alpha = 0.95;
            pitchFiltered = alpha * (pitchFiltered + gyroRateY * dt) + (1.0 - alpha) * rawPitch;
            rollFiltered  = alpha * (rollFiltered  + gyroRateX * dt) + (1.0 - alpha) * rawRoll;

            // Anti-dérive Yaw (fuite lente vers le zéro pour éviter les dérives infinies)
            yawEstimated += gyroRateZ * dt;
            yawEstimated *= 0.998; // fuite anti-dérive
        } else {
            // Pas d'accélération détectée : maintien neutre parfait
            pitchFiltered = 0.0;
            rollFiltered  = 0.0;
            yawEstimated  = 0.0;
        }
    }

    // Zone morte fine (au repos, aucun tremblement)
    if (fabs(pitchFiltered) < 2.0) pitchFiltered = 0.0;
    if (fabs(rollFiltered)  < 2.0) rollFiltered  = 0.0;

    // Bornage de sécurité pour éviter les inversions extravagantes
    pitchFiltered = constrain(pitchFiltered, -60.0, 60.0);
    rollFiltered  = constrain(rollFiltered,  -60.0, 60.0);
    yawEstimated  = constrain(yawEstimated,  -180.0, 180.0);

    // =========================================================================
    // LOCOMOTION DYNAMIQUE DU SERVO DE PIED (TILT-TO-WALK)
    // =========================================================================
    // Si Pitch > 3° : marche avant (le servo oscille pour propulser)
    // Si Pitch < -3° : marche arrière
    // Si à plat : repos strict à 90°
    if (fabs(pitchFiltered) > 3.0) {
        float walkSpeed = (pitchFiltered / 30.0) * 5.0; // vitesse proportionnelle
        walkPhase += walkSpeed * dt * 2.0 * PI;
        float stride = sin(walkPhase);

        // Amplitude proportionnelle à l'inclinaison (jusqu'à ±28°)
        float amp = constrain(fabs(pitchFiltered) * 0.8, 10.0, 28.0);
        targetServoAngle = 90.0 + stride * amp;
    } else {
        // État initial / Neutre : repos stable à 90°
        targetServoAngle = 90.0;
    }

    targetServoAngle = constrain(targetServoAngle, 50.0, 130.0);

    // Lissage servo
    currentServoAngle = currentServoAngle * 0.75 + targetServoAngle * 0.25;
    int servoCommand = (int)(currentServoAngle + 0.5);

    if (abs(servoCommand - lastWrittenAngle) >= 1) {
        servoFoot.write(servoCommand);
        lastWrittenAngle = servoCommand;
    }

    // Télémétrie 50 Hz vers Digital Twin
    Serial.printf("{\"roll\":%.2f,\"pitch\":%.2f,\"yaw\":%.2f,\"servo\":%d}\n",
                  rollFiltered, pitchFiltered, yawEstimated, lastWrittenAngle);

    delay(20);
}