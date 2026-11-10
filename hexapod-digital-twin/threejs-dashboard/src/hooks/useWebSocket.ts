// ============================================================
// useWebSocket.ts — Gateway WebSocket connection hook
// ============================================================
import { useEffect, useRef, useCallback } from 'react';
import { useTwinStore, TelemetryPoint } from '../store/twinStore';
import { DigitalTwinState } from '../types/TwinState';

const GATEWAY_URL = 'ws://localhost:8080';
const MAX_BACKOFF_MS = 10_000;
const PING_INTERVAL_MS = 2_000;

export type SendCommandFn = (command: string, params?: Record<string, unknown>) => void;

interface PingRecord {
  id: number;
  sentAt: number;
}

export function useWebSocket(): { isConnected: boolean; reconnectCount: number; sendCommand: SendCommandFn } {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const backoffRef = useRef(500);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pingMapRef = useRef<Map<number, PingRecord>>(new Map());
  const pingIdRef = useRef(0);
  const startTimeRef = useRef(Date.now());

  const { updateState, setConnected, incrementPacket, addTelemetryPoint, addLatencySample } =
    useTwinStore.getState();

  // ── send a message if socket is open ──────────────────────
  const send = useCallback((payload: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const sendCommand: SendCommandFn = useCallback(
    (command, params) => {
      send({ type: 'COMMAND', command, params: params ?? {} });
    },
    [send]
  );

  // ── handle incoming message ────────────────────────────────
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as Record<string, unknown>;

        if (data.type === 'PONG') {
          const id = data.id as number;
          const record = pingMapRef.current.get(id);
          if (record) {
            const latency = Date.now() - record.sentAt;
            addLatencySample(latency);
            pingMapRef.current.delete(id);
          }
          return;
        }

        if (data.type === 'STATE' || !data.type) {
          const state = data.state as Partial<DigitalTwinState> ?? data as Partial<DigitalTwinState>;
          updateState(state);
          incrementPacket();

          // Build telemetry point
          const elapsed = (Date.now() - startTimeRef.current) / 1000;
          const pt: TelemetryPoint = {
            time: elapsed,
            pitch: state.orientation?.pitch ?? 0,
            roll: state.orientation?.roll ?? 0,
            yaw: state.orientation?.yaw ?? 0,
            servo: state.physicalServo?.angle ?? 90,
            ax: state.imu?.raw?.ax ?? 0,
            ay: state.imu?.raw?.ay ?? 0,
            az: state.imu?.raw?.az ?? 0,
            gx: state.imu?.raw?.gx ?? 0,
            gy: state.imu?.raw?.gy ?? 0,
            gz: state.imu?.raw?.gz ?? 0,
          };
          addTelemetryPoint(pt);
        }
      } catch {
        // Silently ignore malformed packets
      }
    },
    [updateState, incrementPacket, addTelemetryPoint, addLatencySample]
  );

  // ── connect ───────────────────────────────────────────────
  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(GATEWAY_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectCountRef.current = 0;
      backoffRef.current = 500;
      setConnected(true);
      useTwinStore.setState({ connected: true });

      // Start ping loop
      if (pingTimerRef.current) clearInterval(pingTimerRef.current);
      pingTimerRef.current = setInterval(() => {
        const id = ++pingIdRef.current;
        pingMapRef.current.set(id, { id, sentAt: Date.now() });
        send({ type: 'PING', id });
        // Expire stale pings
        pingMapRef.current.forEach((rec, k) => {
          if (Date.now() - rec.sentAt > 5000) pingMapRef.current.delete(k);
        });
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = handleMessage;

    ws.onclose = () => {
      setConnected(false);
      useTwinStore.setState({ connected: false });
      if (pingTimerRef.current) clearInterval(pingTimerRef.current);

      // Exponential backoff reconnect
      const delay = Math.min(backoffRef.current, MAX_BACKOFF_MS);
      backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
      reconnectCountRef.current += 1;
      useTwinStore.setState({ connected: false });
      reconnectTimerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [send, handleMessage, setConnected]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (pingTimerRef.current) clearInterval(pingTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on teardown
        wsRef.current.close();
      }
    };
  }, [connect]);

  const store = useTwinStore();
  return {
    isConnected: store.connected,
    reconnectCount: reconnectCountRef.current,
    sendCommand,
  };
}
