import React from 'react';
import { useTwinStore, OverlayFlags } from '../store/twinStore';

export const OverlayToggles: React.FC = () => {
  const overlays = useTwinStore((s) => s.overlays);
  const toggleOverlay = useTwinStore((s) => s.toggleOverlay);

  const items: { key: keyof OverlayFlags; label: string }[] = [
    { key: 'worldAxes', label: 'World Axes' },
    { key: 'robotAxes', label: 'Robot Axes' },
    { key: 'jointAxes', label: 'Joint Axes' },
    { key: 'legNames', label: 'Leg Labels' },
    { key: 'footPositions', label: 'Foot Points' },
  ];

  return (
    <div className="overlay-floating-panel">
      <div className="overlay-title">3D OVERLAYS</div>
      {items.map((it) => (
        <label key={it.key} className="overlay-item">
          <input
            type="checkbox"
            checked={overlays[it.key]}
            onChange={() => toggleOverlay(it.key)}
          />
          <span>{it.label}</span>
        </label>
      ))}
    </div>
  );
};
