import React from 'react';
import { useTwinStore } from '../store/twinStore';

export const StatusHeader: React.FC = () => {
  const { state, connected, fps } = useTwinStore();
  const esp32Connected = state.connection.esp32;
  const webotsConnected = state.connection.webots;
  const syncStatus = state.twinHealth.syncStatus;
  const mode = state.mode;
  const hz = state.twinHealth.telemetryHz;
  const latency = state.twinHealth.latencyMs;

  const getSyncColor = () => {
    if (syncStatus === 'SYNC_GOOD') return '#4caf50';
    if (syncStatus === 'SYNC_DEGRADED') return '#ff9800';
    return '#f44336';
  };

  return (
    <header className="status-header">
      <div className="header-title">
        <span className="logo-hex">⬡</span>
        <span className="title-text">HEXAPOD DIGITAL TWIN</span>
        <span className="system-pill" style={{ borderColor: connected ? '#4caf50' : '#f44336' }}>
          GATEWAY: <strong style={{ color: connected ? '#4caf50' : '#f44336' }}>{connected ? 'ONLINE' : 'OFFLINE'}</strong>
        </span>
      </div>

      <div className="header-status-items">
        <div className="status-item">
          <span className="status-label">ESP32</span>
          <span className="status-badge" style={{ backgroundColor: esp32Connected ? '#4caf50' : '#333' }}>
            {esp32Connected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">WEBOTS</span>
          <span className="status-badge" style={{ backgroundColor: webotsConnected ? '#4caf50' : '#333' }}>
            {webotsConnected ? 'RUNNING' : 'STOPPED'}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">SYNC</span>
          <span className="status-badge" style={{ backgroundColor: getSyncColor() }}>
            {syncStatus}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">MODE</span>
          <span className="mode-pill">{mode}</span>
        </div>

        <div className="metrics-group">
          <span>{hz.toFixed(1)} Hz</span>
          <span className="divider">|</span>
          <span>{latency.toFixed(0)} ms</span>
          <span className="divider">|</span>
          <span>{fps} FPS</span>
        </div>
      </div>
    </header>
  );
};
