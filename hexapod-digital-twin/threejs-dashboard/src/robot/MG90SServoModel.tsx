import React from 'react';
import * as THREE from 'three';

interface MG90SServoProps {
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
  hornAngleRad?: number;
  wireframe?: boolean;
}

/**
 * MG90S High-Precision Micro-Servo 3D Model
 * Replicating real dimensions (~22.8mm x 12.2mm x 28.5mm),
 * composite dark body, mounting tabs with brass eyelets,
 * raised gear tower, brass splined output shaft and horn.
 */
export const MG90SServoModel: React.FC<MG90SServoProps> = ({
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  scale = 1.0,
  hornAngleRad = 0,
  wireframe = false,
}) => {
  // Servo Materials
  const bodyMaterial = React.useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#1a1d20',
        roughness: 0.7,
        metalness: 0.15,
        wireframe,
      }),
    [wireframe]
  );

  const brassMaterial = React.useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#d4af37',
        roughness: 0.25,
        metalness: 0.85,
        wireframe,
      }),
    [wireframe]
  );

  const hardwareMaterial = React.useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#94a3b8',
        roughness: 0.3,
        metalness: 0.9,
        wireframe,
      }),
    [wireframe]
  );

  const hornMaterial = React.useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#f8fafc',
        roughness: 0.5,
        metalness: 0.1,
        wireframe,
      }),
    [wireframe]
  );

  return (
    <group position={position} rotation={rotation} scale={scale}>
      {/* Main Servo Case Body (22.8 x 12.2 x 22 mm main box) */}
      <mesh position={[0, 0, 0]} material={bodyMaterial} castShadow receiveShadow>
        <boxGeometry args={[0.0122, 0.022, 0.0228]} />
      </mesh>

      {/* Top Gear Housing Cap (raised step) */}
      <mesh position={[0, 0.011 + 0.002, 0.003]} material={bodyMaterial} castShadow>
        <boxGeometry args={[0.0122, 0.004, 0.016]} />
      </mesh>

      {/* Raised Round Gear Tower for Output Spline */}
      <mesh position={[0, 0.0145, 0.0055]} material={bodyMaterial} castShadow>
        <cylinderGeometry args={[0.0055, 0.0055, 0.003, 16]} />
      </mesh>

      {/* Mounting Flange / Tabs (32.2mm length across) */}
      <mesh position={[0, 0.006, 0]} material={bodyMaterial} castShadow>
        <boxGeometry args={[0.0122, 0.0022, 0.0322]} />
      </mesh>

      {/* Brass Eyelet Bushings in Mounting Ears */}
      <mesh position={[0, 0.006, 0.0135]} material={brassMaterial}>
        <cylinderGeometry args={[0.0015, 0.0015, 0.0025, 12]} />
      </mesh>
      <mesh position={[0, 0.006, -0.0135]} material={brassMaterial}>
        <cylinderGeometry args={[0.0015, 0.0015, 0.0025, 12]} />
      </mesh>

      {/* Servo Wire Exit Boot (Ribbon Cable exiting bottom side) */}
      <mesh position={[0, -0.010, -0.009]} material={bodyMaterial}>
        <boxGeometry args={[0.004, 0.003, 0.004]} />
      </mesh>

      {/* Output Spline (Brass/Metal shaft) */}
      <group position={[0, 0.0165, 0.0055]}>
        <mesh material={brassMaterial} castShadow>
          <cylinderGeometry args={[0.0024, 0.0024, 0.003, 16]} />
        </mesh>

        {/* Servo Horn Assembly (rotates with hornAngleRad) */}
        <group rotation={[0, hornAngleRad, 0]}>
          {/* Central Hub */}
          <mesh position={[0, 0.002, 0]} material={hornMaterial} castShadow>
            <cylinderGeometry args={[0.004, 0.004, 0.002, 16]} />
          </mesh>
          {/* Arm link */}
          <mesh position={[0, 0.002, 0.007]} material={hornMaterial} castShadow>
            <boxGeometry args={[0.004, 0.0018, 0.012]} />
          </mesh>
          {/* Center Horn Retaining Machine Screw */}
          <mesh position={[0, 0.0032, 0]} material={hardwareMaterial}>
            <cylinderGeometry args={[0.0014, 0.0014, 0.0006, 12]} />
          </mesh>
        </group>
      </group>
    </group>
  );
};

