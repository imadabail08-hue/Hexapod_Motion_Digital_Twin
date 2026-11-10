import React from 'react';
import { useTwinStore } from '../store/twinStore';

export const TwinHealth: React.FC = () => {
  const health = useTwinStore((s) => s.state.twinHealth);

  return (
    <div className="twin-health-bar">
      <div className="health-metric">
        <span className="metric-label">PACKET AGE</span>
        <span className="metric-val">{health.packetAgeMs.toFixed(0)} ms</span>
      </div>
      <div className="health-metric">
        <span className="metric-label">EST. LATENCY</span>
        <span className="metric-val">{health.latencyMs.toFixed(0)} ms</span>
      </div>
      <div className="health-metric">
        <span className="metric-label">MAX SERVO ERROR</span>
        <span className="metric-val cyan">{health.maxServoError.toFixed(1)}°</span>
      </div>
      <div className="health-metric">
        <span className="metric-label">SIM REAL-TIME FACTOR</span>
        <span className="metric-val green">{health.simulationRTF.toFixed(2)}x</span>
      </div>
      <div className="health-metric">
        <span className="metric-label">PACKET LOSS</span>
        <span className="metric-val">{health.packetLoss.toFixed(1)}%</span>
      </div>
    </div>
  );
};
