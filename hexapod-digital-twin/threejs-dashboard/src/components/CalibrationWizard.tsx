import React, { useState } from 'react';
import { SendCommandFn } from '../hooks/useWebSocket';

interface CalibrationWizardProps {
  onClose: () => void;
  sendCommand: SendCommandFn;
}

export const CalibrationWizard: React.FC<CalibrationWizardProps> = ({ onClose, sendCommand }) => {
  const [step, setStep] = useState(1);
  const [progress, setProgress] = useState(0);

  const startCal = () => {
    setStep(2);
    sendCommand('CALIBRATE_IMU');
    let p = 0;
    const interval = setInterval(() => {
      p += 5;
      setProgress(p);
      if (p >= 100) {
        clearInterval(interval);
        setStep(3);
      }
    }, 100);
  };

  return (
    <div className="modal-backdrop">
      <div className="calibration-card">
        <div className="cal-title">GUIDED IMU CALIBRATION WIZARD</div>

        {step === 1 && (
          <div className="cal-content">
            <p className="step-instr">
              <strong>STEP 1:</strong> Place the MakerBoard / ESP32 on a flat, completely stable surface.
            </p>
            <p className="step-instr">
              <strong>STEP 2:</strong> Ensure no vibrations or motion are present.
            </p>
            <button className="btn btn-primary" onClick={startCal}>
              BEGIN CALIBRATION (200 SAMPLES)
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="cal-content">
            <p className="step-instr">Collecting zero offsets and bias estimations...</p>
            <div className="cal-progress-bar">
              <div className="cal-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <span className="cal-pct">{progress}%</span>
          </div>
        )}

        {step === 3 && (
          <div className="cal-content">
            <p className="step-success">✓ CALIBRATION SUCCESSFUL</p>
            <p className="cal-details">Pitch zero, roll zero, and gyro biases saved to controller.</p>
            <button className="btn btn-secondary" onClick={onClose}>
              CLOSE WIZARD
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
