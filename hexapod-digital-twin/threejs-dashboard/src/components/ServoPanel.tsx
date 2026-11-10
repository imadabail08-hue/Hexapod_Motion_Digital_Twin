import React from 'react';
import { useTwinStore } from '../store/twinStore';
import { SERVO_NAMES, LEG_NAMES } from '../types/ServoMap';

export const ServoPanel: React.FC = () => {
  const virtualServos = useTwinStore((s) => s.state.virtualServos);
  const simulatedServos = useTwinStore((s) => s.state.simulatedServos);
  const servoErrors = useTwinStore((s) => s.state.servoErrors);
  const physicalServo = useTwinStore((s) => s.state.physicalServo);

  return (
    <div className="panel servo-panel">
      <div className="panel-header">18-DOF ACTUATORS</div>

      <div className="physical-servo-card">
        <div className="card-label">PHYSICAL HARDWARE (MG90S)</div>
        <div className="card-row">
          <span>Angle: <strong>{physicalServo.angle}°</strong></span>
          <span>Command: <strong>{physicalServo.command}°</strong></span>
          <span className="badge-safe">SAFE [50°–130°]</span>
        </div>
      </div>

      <div className="legs-container">
        {LEG_NAMES.map((leg, legIdx) => {
          return (
            <div key={leg} className="leg-group">
              <div className="leg-header">{leg} LEG</div>
              {[0, 1, 2].map((jointIdx) => {
                const sId = legIdx * 3 + jointIdx;
                const vAngle = virtualServos[sId] ?? 90;
                const sAngle = simulatedServos[sId] ?? 90;
                const err = servoErrors[sId] ?? 0;
                const name = SERVO_NAMES[sId] ?? `S${sId}`;

                return (
                  <div key={sId} className="servo-row">
                    <span className="servo-name">{name.replace(`${leg}_`, '')}</span>
                    <div className="servo-bar-bg">
                      <div
                        className="servo-bar-fill"
                        style={{ width: `${Math.min(100, Math.max(0, (vAngle / 180) * 100))}%` }}
                      />
                    </div>
                    <span className="servo-val">{vAngle.toFixed(0)}°</span>
                    <span
                      title={`Sim: ${sAngle.toFixed(0)}°`}
                      className={`servo-err ${err > 3 ? 'err-high' : err > 1 ? 'err-med' : 'err-low'}`}
                    >
                      ±{err.toFixed(1)}°
                    </span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

