import React from 'react';
import { OrbitControls } from '@react-three/drei';

export const CameraControls: React.FC = () => {
  return (
    <OrbitControls
      makeDefault
      enableDamping
      dampingFactor={0.05}
      minDistance={0.3}
      maxDistance={3.0}
      target={[0, 0, 0]}
    />
  );
};
