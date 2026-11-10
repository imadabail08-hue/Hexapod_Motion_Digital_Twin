import React from 'react';
import { useTwinStore } from '../store/twinStore';

export const OrientationPanel: React.FC = () => {
  const orientation = useTwinStore((s) => s.state.orientation);
  const imu = useTwinStore((s) => s.state.imu.raw);

  const accelMag = Math.sqrt(
    imu.ax * imu.ax + imu.ay * imu.ay + imu.az * imu.az
  ).toFixed(2);

  return (
    <div className="panel orientation-panel">
      <div className="panel-header">BODY ORIENTATION</div>

      <div className="rpy-grid">
        <div className="rpy-card">
          <div className="rpy-label">PITCH</div>
          <div className="rpy-value cyan">{orientation.pitch.toFixed(1)}°</div>
          <div className="rpy-sub">X-Axis Tilt</div>
        </div>

        <div className="rpy-card">
          <div className="rpy-label">ROLL</div>
          <div className="rpy-value green">{orientation.roll.toFixed(1)}°</div>
          <div className="rpy-sub">Y-Axis Roll</div>
        </div>

        <div className="rpy-card">
          <div className="rpy-label">YAW</div>
          <div className="rpy-value amber">{orientation.yaw.toFixed(1)}°</div>
          <div className="drift-warning">GYRO-INTEGRATED (Drift expected)</div>
        </div>
      </div>

      <div className="panel-section-title">RAW ACCELEROMETER (m/s²)</div>
      <div className="sensor-readout-row">
        <span>X: <strong>{imu.ax.toFixed(2)}</strong></span>
        <span>Y: <strong>{imu.ay.toFixed(2)}</strong></span>
        <span>Z: <strong>{imu.az.toFixed(2)}</strong></span>
      </div>
      <div className="mag-row">
        Magnitude |a|: <strong>{accelMag} m/s²</strong>
      </div>

      <div className="panel-section-title">RAW GYROSCOPE (°/s)</div>
      <div className="sensor-readout-row">
        <span>X: <strong>{imu.gx.toFixed(1)}</strong></span>
        <span>Y: <strong>{imu.gy.toFixed(1)}</strong></span>
        <span>Z: <strong>{imu.gz.toFixed(1)}</strong></span>
      </div>
    </div>
  );
};
