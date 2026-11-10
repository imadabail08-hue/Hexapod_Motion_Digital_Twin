import React, { useState } from 'react';
import { SendCommandFn } from '../hooks/useWebSocket';

interface ManualControlProps {
  sendCommand: SendCommandFn;
}

export const ManualControl: React.FC<ManualControlProps> = ({ sendCommand }) => {
  const [hwEnabled, setHwEnabled] = useState(false);
  const [pitch, setPitch] = useState(0);
  const [roll, setRoll] = useState(0);

  const handlePitchChange = (val: number) => {
    setPitch(val);
    if (hwEnabled) {
      sendCommand('SET_ORIENTATION', { pitch: val, roll });
    }
  };

  const handleRollChange = (val: number) => {
    setRoll(val);
    if (hwEnabled) {
      sendCommand('SET_ORIENTATION', { pitch, roll: val });
    }
  };

  return (
    <div className="manual-control-modal">
      <div className="modal-header">
        <span>MANUAL ROBOT ENGINEERING CONTROL</span>
        <label className="hw-gate-toggle">
          <input
            type="checkbox"
            checked={hwEnabled}
            onChange={(e) => setHwEnabled(e.target.checked)}
          />
          <span className="hw-gate-text">HARDWARE COMMAND ENABLE</span>
        </label>
      </div>

      <div className="sliders-container">
        <div className="slider-group">
          <label>Pitch Target: {pitch}°</label>
          <input
            type="range"
            min="-40"
            max="40"
            value={pitch}
            onChange={(e) => handlePitchChange(Number(e.target.value))}
          />
        </div>

        <div className="slider-group">
          <label>Roll Target: {roll}°</label>
          <input
            type="range"
            min="-40"
            max="40"
            value={roll}
            onChange={(e) => handleRollChange(Number(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
};

