// ============================================================
// twinStore.ts — Zustand global state store
// ============================================================
import { create } from 'zustand';
import { DigitalTwinState, DEFAULT_TWIN_STATE } from '../types/TwinState';

export interface TelemetryPoint {
  time: number;   // relative seconds
  pitch: number;
  roll: number;
  yaw: number;
  servo: number;  // physical servo angle
  ax: number;
  ay: number;
  az: number;
  gx: number;
  gy: number;
  gz: number;
}

export interface OverlayFlags {
  worldAxes: boolean;
  robotAxes: boolean;
  imuAxes: boolean;
  jointAxes: boolean;
  servoNumbers: boolean;
  legNames: boolean;
  footPositions: boolean;
  contacts: boolean;
  cog: boolean;
}

export interface TwinStore {
  // Core state
  state: DigitalTwinState;
  connected: boolean;
  mode: string;
  packetCount: number;
  fps: number;

  // History
  latencyHistory: number[];          // max 100 entries
  telemetryHistory: TelemetryPoint[]; // max 1000 entries

  // 3D overlay toggles
  overlays: OverlayFlags;

  // Actions
  updateState: (next: Partial<DigitalTwinState>) => void;
  setConnected: (connected: boolean) => void;
  incrementPacket: () => void;
  addTelemetryPoint: (pt: TelemetryPoint) => void;
  setFPS: (fps: number) => void;
  addLatencySample: (ms: number) => void;
  toggleOverlay: (key: keyof OverlayFlags) => void;
}

const MAX_LATENCY_HISTORY = 100;
const MAX_TELEMETRY_HISTORY = 1000;

export const useTwinStore = create<TwinStore>((set) => ({
  state: DEFAULT_TWIN_STATE,
  connected: false,
  mode: 'IDLE',
  packetCount: 0,
  fps: 0,
  latencyHistory: [],
  telemetryHistory: [],

  overlays: {
    worldAxes: true,
    robotAxes: false,
    imuAxes: false,
    jointAxes: false,
    servoNumbers: false,
    legNames: true,
    footPositions: true,
    contacts: true,
    cog: false,
  },

  updateState: (next) =>
    set((store) => ({
      state: { ...store.state, ...next },
      mode: next.mode ?? store.mode,
    })),

  setConnected: (connected) => set({ connected }),

  incrementPacket: () =>
    set((store) => ({ packetCount: store.packetCount + 1 })),

  addTelemetryPoint: (pt) =>
    set((store) => {
      const history = store.telemetryHistory;
      const next =
        history.length >= MAX_TELEMETRY_HISTORY
          ? [...history.slice(1), pt]
          : [...history, pt];
      return { telemetryHistory: next };
    }),

  setFPS: (fps) => set({ fps }),

  addLatencySample: (ms) =>
    set((store) => {
      const hist = store.latencyHistory;
      const next =
        hist.length >= MAX_LATENCY_HISTORY
          ? [...hist.slice(1), ms]
          : [...hist, ms];
      return { latencyHistory: next };
    }),

  toggleOverlay: (key) =>
    set((store) => ({
      overlays: { ...store.overlays, [key]: !store.overlays[key] },
    })),
}));
