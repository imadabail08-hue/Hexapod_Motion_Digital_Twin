// ============================================================
// TwinState.ts — TypeScript interfaces matching Gateway Pydantic models
// ============================================================

export interface ImuRaw {
  ax: number;
  ay: number;
  az: number;
  gx: number;
  gy: number;
  gz: number;
}

export interface ImuData {
  raw: ImuRaw;
  filtered: ImuRaw;
}

export interface Orientation {
  pitch: number;
  roll: number;
  yaw: number;
  yawAbsolute?: boolean;
  pitchZero?: number;
  rollZero?: number;
}

export interface PhysicalServo {
  id: number;
  angle: number;
  command: number;
  min: number;
  max: number;
}

export interface FootPosition {
  leg: string;
  x: number;
  y: number;
  z: number;
  inContact?: boolean;
}

export interface ConnectionStatus {
  esp32: boolean;
  webots: boolean;
  clientCount: number;
}

export interface TwinHealth {
  syncStatus: string;
  packetAgeMs: number;
  latencyMs: number;
  telemetryHz: number;
  packetLoss: number;
  orientationErrorPitch: number;
  orientationErrorRoll: number;
  maxServoError: number;
  simulationRTF: number;
}

export interface DigitalTwinState {
  timestamp: number;
  sequence: number;
  mode: string;
  emergencyStop: boolean;
  stabilization: boolean;
  connection: ConnectionStatus;
  imu: ImuData;
  orientation: Orientation;
  physicalServo: PhysicalServo;
  virtualServos: number[];
  simulatedServos: number[];
  servoErrors: number[];
  footPositions: FootPosition[];
  twinHealth: TwinHealth;
}

export const DEFAULT_TWIN_STATE: DigitalTwinState = {
  timestamp: Date.now(),
  sequence: 0,
  mode: 'SIMULATION',
  emergencyStop: false,
  stabilization: true,

  connection: {
    esp32: false,
    webots: false,
    clientCount: 0,
  },

  imu: {
    raw: { ax: 0, ay: 0, az: 9.81, gx: 0, gy: 0, gz: 0 },
    filtered: { ax: 0, ay: 0, az: 9.81, gx: 0, gy: 0, gz: 0 },
  },

  orientation: { pitch: 0, roll: 0, yaw: 0, yawAbsolute: false, pitchZero: 0, rollZero: 0 },

  physicalServo: { id: 1, angle: 90, command: 90, min: 50, max: 130 },

  virtualServos: Array(18).fill(90),
  simulatedServos: Array(18).fill(90),
  servoErrors: Array(18).fill(0),

  footPositions: [
    { leg: 'LF', x: 0, y: 0, z: 0 },
    { leg: 'RF', x: 0, y: 0, z: 0 },
    { leg: 'LM', x: 0, y: 0, z: 0 },
    { leg: 'RM', x: 0, y: 0, z: 0 },
    { leg: 'LR', x: 0, y: 0, z: 0 },
    { leg: 'RR', x: 0, y: 0, z: 0 },
  ],

  twinHealth: {
    syncStatus: 'SYNC_LOST',
    packetAgeMs: 9999,
    latencyMs: 0,
    telemetryHz: 0,
    packetLoss: 0,
    orientationErrorPitch: 0,
    orientationErrorRoll: 0,
    maxServoError: 0,
    simulationRTF: 1.0,
  },
};
