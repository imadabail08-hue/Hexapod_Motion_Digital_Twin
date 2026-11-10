import React from 'react';
import { useTwinStore } from '../store/twinStore';

export const SceneSetup: React.FC = () => {
  const worldAxes = useTwinStore((s) => s.overlays.worldAxes);

  return (
    <>
      <color attach="background" args={['#1a1a1a']} />
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[5, 10, 5]}
        intensity={1.2}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <pointLight position={[-5, 5, -5]} intensity={0.6} color="#00bcd4" />
      <gridHelper args={[4, 20, '#00bcd4', '#333333']} position={[0, -0.15, 0]} />
      {worldAxes && <axesHelper args={[0.5]} position={[0, -0.14, 0]} />}
    </>
  );
};
