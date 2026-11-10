// ============================================================
// useTelemetry.ts — Telemetry frequency, FPS, sync status
// ============================================================
import { useEffect, useRef, useState, useCallback } from 'react';
import { useTwinStore } from '../store/twinStore';

export type SyncStatus = 'GOOD' | 'DEGRADED' | 'LOST';

export interface TelemetryMetrics {
  telemetryHz: number;
  fps: number;
  latencyMs: number;
  syncStatus: SyncStatus;
}

const ROLLING_WINDOW_S = 5;
const UPDATE_INTERVAL_MS = 500;

export function useTelemetry(): TelemetryMetrics {
  const packetTimestampsRef = useRef<number[]>([]);
  const frameTimestampsRef = useRef<number[]>([]);
  const rafHandleRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [metrics, setMetrics] = useState<TelemetryMetrics>({
    telemetryHz: 0,
    fps: 0,
    latencyMs: 0,
    syncStatus: 'LOST',
  });

  const packetCount = useTwinStore((s) => s.packetCount);
  const latencyHistory = useTwinStore((s) => s.latencyHistory);

  // Track new packets
  useEffect(() => {
    packetTimestampsRef.current.push(Date.now());
  }, [packetCount]);

  // RAF frame counter
  const countFrame = useCallback(() => {
    frameTimestampsRef.current.push(Date.now());
    rafHandleRef.current = requestAnimationFrame(countFrame);
  }, []);

  useEffect(() => {
    rafHandleRef.current = requestAnimationFrame(countFrame);
    return () => cancelAnimationFrame(rafHandleRef.current);
  }, [countFrame]);

  // Compute metrics on interval
  useEffect(() => {
    const compute = () => {
      const now = Date.now();
      const windowMs = ROLLING_WINDOW_S * 1000;
      const cutoff = now - windowMs;

      // Prune old timestamps
      packetTimestampsRef.current = packetTimestampsRef.current.filter((t) => t > cutoff);
      frameTimestampsRef.current = frameTimestampsRef.current.filter((t) => t > cutoff);

      const telemetryHz = packetTimestampsRef.current.length / ROLLING_WINDOW_S;
      const fps = frameTimestampsRef.current.length / ROLLING_WINDOW_S;

      const latencyMs =
        latencyHistory.length > 0
          ? latencyHistory.reduce((a, b) => a + b, 0) / latencyHistory.length
          : 0;

      let syncStatus: SyncStatus;
      if (telemetryHz >= 8) {
        syncStatus = 'GOOD';
      } else if (telemetryHz >= 2) {
        syncStatus = 'DEGRADED';
      } else {
        syncStatus = 'LOST';
      }

      setMetrics({ telemetryHz, fps, latencyMs, syncStatus });
    };

    intervalRef.current = setInterval(compute, UPDATE_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [latencyHistory]);

  return metrics;
}
