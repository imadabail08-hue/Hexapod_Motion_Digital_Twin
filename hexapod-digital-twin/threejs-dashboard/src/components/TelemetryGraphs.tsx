import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { useTwinStore } from '../store/twinStore';

type GraphTab = 'ORIENTATION' | 'ACCEL' | 'GYRO' | 'SERVO';

export const TelemetryGraphs: React.FC = () => {
  const [tab, setTab] = useState<GraphTab>('ORIENTATION');
  const history = useTwinStore((s) => s.telemetryHistory);

  // Take the last 150 points for performance
  const data = history.slice(-150);

  return (
    <div className="telemetry-graphs-container">
      <div className="graphs-header">
        <span className="graphs-title">REAL-TIME TELEMETRY (ROLLING BUFFER)</span>
        <div className="tab-buttons">
          <button
            className={`tab-btn ${tab === 'ORIENTATION' ? 'active' : ''}`}
            onClick={() => setTab('ORIENTATION')}
          >
            ORIENTATION
          </button>
          <button
            className={`tab-btn ${tab === 'ACCEL' ? 'active' : ''}`}
            onClick={() => setTab('ACCEL')}
          >
            ACCELEROMETER
          </button>
          <button
            className={`tab-btn ${tab === 'GYRO' ? 'active' : ''}`}
            onClick={() => setTab('GYRO')}
          >
            GYROSCOPE
          </button>
          <button
            className={`tab-btn ${tab === 'SERVO' ? 'active' : ''}`}
            onClick={() => setTab('SERVO')}
          >
            PHYSICAL SERVO
          </button>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={160}>
          {tab === 'ORIENTATION' ? (
            <LineChart data={data}>
              <XAxis dataKey="time" stroke="#666" tick={{ fontSize: 10 }} />
              <YAxis domain={[-45, 45]} stroke="#666" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#222', borderColor: '#444' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="pitch" stroke="#00bcd4" dot={false} strokeWidth={2} name="Pitch (°)" />
              <Line type="monotone" dataKey="roll" stroke="#4caf50" dot={false} strokeWidth={2} name="Roll (°)" />
              <Line type="monotone" dataKey="yaw" stroke="#ff9800" dot={false} strokeWidth={1} strokeDasharray="3 3" name="Yaw [Drift] (°)" />
            </LineChart>
          ) : tab === 'ACCEL' ? (
            <LineChart data={data}>
              <XAxis dataKey="time" stroke="#666" tick={{ fontSize: 10 }} />
              <YAxis stroke="#666" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#222', borderColor: '#444' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="ax" stroke="#f44336" dot={false} name="Ax (m/s²)" />
              <Line type="monotone" dataKey="ay" stroke="#4caf50" dot={false} name="Ay (m/s²)" />
              <Line type="monotone" dataKey="az" stroke="#2196f3" dot={false} name="Az (m/s²)" />
            </LineChart>
          ) : tab === 'GYRO' ? (
            <LineChart data={data}>
              <XAxis dataKey="time" stroke="#666" tick={{ fontSize: 10 }} />
              <YAxis stroke="#666" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#222', borderColor: '#444' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="gx" stroke="#f44336" dot={false} name="Gx (°/s)" />
              <Line type="monotone" dataKey="gy" stroke="#4caf50" dot={false} name="Gy (°/s)" />
              <Line type="monotone" dataKey="gz" stroke="#2196f3" dot={false} name="Gz (°/s)" />
            </LineChart>
          ) : (
            <LineChart data={data}>
              <XAxis dataKey="time" stroke="#666" tick={{ fontSize: 10 }} />
              <YAxis domain={[40, 140]} stroke="#666" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#222', borderColor: '#444' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="servo" stroke="#ff9800" dot={false} strokeWidth={2} name="MG90S Angle (°)" />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
