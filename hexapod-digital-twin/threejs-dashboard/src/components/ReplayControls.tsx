import React from 'react';
import { SendCommandFn } from '../hooks/useWebSocket';

interface ReplayControlsProps {
  sendCommand: SendCommandFn;
}

export const ReplayControls: React.FC<ReplayControlsProps> = ({ sendCommand }) => {
  return (
    <div className="replay-bar">
      <span className="replay-label">TELEMETRY REPLAY MODE</span>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_PLAY')}>
        ▶ PLAY
      </button>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_PAUSE')}>
        ⏸ PAUSE
      </button>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_RESTART')}>
        ↺ RESTART
      </button>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_SPEED', { speed: 0.5 })}>
        0.5x
      </button>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_SPEED', { speed: 1.0 })}>
        1.0x
      </button>
      <button className="btn btn-secondary" onClick={() => sendCommand('REPLAY_SPEED', { speed: 2.0 })}>
        2.0x
      </button>
    </div>
  );
};
