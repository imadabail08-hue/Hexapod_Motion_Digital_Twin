import React, { useState } from 'react';
import { useTwinStore } from '../store/twinStore';
import { SendCommandFn } from '../hooks/useWebSocket';

interface CommandBarProps {
  sendCommand: SendCommandFn;
  onOpenCalibration: () => void;
}

export const CommandBar: React.FC<CommandBarProps> = ({ sendCommand, onOpenCalibration }) => {
  const mode = useTwinStore((s) => s.state.mode);
  const emergencyStop = useTwinStore((s) => s.state.emergencyStop);
  const [recording, setRecording] = useState(false);

  const handleEStopToggle = () => {
    if (emergencyStop) {
      sendCommand('RESET_EMERGENCY_STOP');
    } else {
      sendCommand('EMERGENCY_STOP');
    }
  };

  const handleToggleRecording = () => {
    if (recording) {
      sendCommand('STOP_RECORDING');
      setRecording(false);
    } else {
      sendCommand('START_RECORDING');
      setRecording(true);
    }
  };

  return (
    <div className={`command-bar ${emergencyStop ? 'estop-active' : ''}`}>
      <div className="btn-group-left">
        <button className="btn btn-secondary" onClick={onOpenCalibration}>
          CALIBRATE IMU
        </button>
        <button className="btn btn-secondary" onClick={() => sendCommand('RESET_YAW')}>
          RESET YAW
        </button>
        <button className="btn btn-secondary" onClick={() => sendCommand('CENTER_SERVO')}>
          CENTER SERVO
        </button>
        <button
          className={`btn ${mode === 'MIRROR_18' ? 'btn-active' : 'btn-secondary'}`}
          onClick={() => sendCommand('ENABLE_MIRROR_18')}
        >
          MIRROR 18 MODE
        </button>
        <button
          className={`btn ${mode === 'SIMULATION' ? 'btn-active' : 'btn-secondary'}`}
          onClick={() => sendCommand('SET_MODE', { mode: 'SIMULATION' })}
        >
          SIM MODE
        </button>
        <button
          className={`btn ${recording ? 'btn-rec-active' : 'btn-secondary'}`}
          onClick={handleToggleRecording}
        >
          {recording ? '● RECORDING (STOP)' : '○ START RECORDING'}
        </button>
      </div>

      <div className="btn-group-right">
        <button
          className={`btn btn-estop ${emergencyStop ? 'pulsing' : ''}`}
          onClick={handleEStopToggle}
        >
          {emergencyStop ? '⚠ RESET EMERGENCY STOP' : '🛑 EMERGENCY STOP'}
        </button>
      </div>
    </div>
  );
};
