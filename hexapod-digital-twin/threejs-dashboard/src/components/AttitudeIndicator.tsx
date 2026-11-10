import React from 'react';

interface AttitudeIndicatorProps {
  pitch: number;
  roll: number;
}

export const AttitudeIndicator: React.FC<AttitudeIndicatorProps> = ({ pitch, roll }) => {
  const r = 45; // radius
  const cx = 55;
  const cy = 55;

  // Clamp pitch visual displacement
  const pitchPx = Math.max(-r + 8, Math.min(r - 8, pitch * 1.2));

  return (
    <div className="attitude-indicator-card">
      <div className="attitude-title">ATTITUDE INDICATOR</div>
      <div className="attitude-dial-wrapper">
        <svg width="110" height="110" viewBox="0 0 110 110">
          <defs>
            <clipPath id="dialClip">
              <circle cx={cx} cy={cy} r={r} />
            </clipPath>
          </defs>

          {/* Outer Ring */}
          <circle cx={cx} cy={cy} r={r + 3} fill="#0d141f" stroke="#23324d" strokeWidth="3" />

          {/* Rotating Horizon Horizon Disc */}
          <g clipPath="url(#dialClip)">
            <g transform={`rotate(${-roll}, ${cx}, ${cy})`}>
              {/* Sky (Blue/Cyan) */}
              <rect x="0" y="0" width="110" height="110" fill="#1e3a5f" />
              {/* Ground (Earth Brown / Charcoal) */}
              <rect x="0" y={cy + pitchPx} width="110" height="110" fill="#3b2318" />
              {/* Horizon dividing line */}
              <line x1="0" y1={cy + pitchPx} x2="110" y2={cy + pitchPx} stroke="#00e5ff" strokeWidth="2" />
              {/* Pitch Ladder bars */}
              <line x1={cx - 15} y1={cy + pitchPx - 15} x2={cx + 15} y2={cy + pitchPx - 15} stroke="#80deea" strokeWidth="1.5" />
              <line x1={cx - 10} y1={cy + pitchPx - 30} x2={cx + 10} y2={cy + pitchPx - 30} stroke="#80deea" strokeWidth="1" />
              <line x1={cx - 15} y1={cy + pitchPx + 15} x2={cx + 15} y2={cy + pitchPx + 15} stroke="#80deea" strokeWidth="1.5" />
              <line x1={cx - 10} y1={cy + pitchPx + 30} x2={cx + 10} y2={cy + pitchPx + 30} stroke="#80deea" strokeWidth="1" />
            </g>
          </g>

          {/* Fixed Center Aircraft Symbol */}
          <path
            d={`M ${cx - 20} ${cy} L ${cx - 6} ${cy} L ${cx - 6} ${cy + 4} M ${cx + 6} ${cy + 4} L ${cx + 6} ${cy} L ${cx + 20} ${cy}`}
            stroke="#00ffcc"
            strokeWidth="2.5"
            fill="none"
          />
          <circle cx={cx} cy={cy} r="3" fill="#00ffcc" />
        </svg>
      </div>
    </div>
  );
};
