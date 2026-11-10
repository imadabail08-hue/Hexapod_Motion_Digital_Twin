// ============================================================
// LegAssembly.tsx — Single leg (Coxa → Femur → Tibia) in R3F
// ============================================================
import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { servoAngleToVisualAngle } from './JointConfig';
import { LEG_NAMES } from '../types/ServoMap';

// Segment dimensions (metres)
const COXA_LENGTH  = 0.053;
const FEMUR_LENGTH = 0.066;
const TIBIA_LENGTH = 0.090;
const SEG_W = 0.012; // cross-section width
const JOINT_R = 0.009;

const METAL_COLOR   = '#2c2c2c';
const JOINT_COLOR   = '#e65100';
const FOOT_COLOR    = '#ff9800';
const CONTACT_COLOR = '#4caf50';

interface LegAssemblyProps {
  legIndex: number;             // 0–5
  servoAngles: [number, number, number];  // [coxa, femur, tibia] command degrees
  showAxes?: boolean;
  showNumbers?: boolean;
  showLegName?: boolean;
  showFootPosition?: boolean;
  inContact?: boolean;
}

// Reusable materials (created once)
const metalMat = new THREE.MeshStandardMaterial({
  color: METAL_COLOR,
  roughness: 0.7,
  metalness: 0.5,
});
const jointMat = new THREE.MeshStandardMaterial({
  color: JOINT_COLOR,
  roughness: 0.4,
  metalness: 0.8,
  emissive: JOINT_COLOR,
  emissiveIntensity: 0.15,
});
const footMat = new THREE.MeshStandardMaterial({
  color: FOOT_COLOR,
  roughness: 0.5,
  metalness: 0.2,
});
const contactMat = new THREE.MeshStandardMaterial({
  color: CONTACT_COLOR,
  roughness: 0.5,
  metalness: 0.2,
  emissive: CONTACT_COLOR,
  emissiveIntensity: 0.4,
});

export const LegAssembly: React.FC<LegAssemblyProps> = React.memo(({
  legIndex,
  servoAngles,
  showAxes = false,
  showNumbers = false,
  showLegName = false,
  showFootPosition = false,
  inContact = false,
}) => {
  const coxaGroupRef  = useRef<THREE.Group>(null);
  const femurGroupRef = useRef<THREE.Group>(null);
  const tibiaGroupRef = useRef<THREE.Group>(null);

  // Current visual angles (smoothly interpolated)
  const visualAnglesRef = useRef<[number, number, number]>([0, 0, 0]);

  const baseServoId = legIndex * 3; // servo IDs: base, base+1, base+2

  useFrame(() => {
    const targetAngles: [number, number, number] = [
      servoAngleToVisualAngle(baseServoId,     servoAngles[0]),
      servoAngleToVisualAngle(baseServoId + 1, servoAngles[1]),
      servoAngleToVisualAngle(baseServoId + 2, servoAngles[2]),
    ];

    // LERP toward target — never snap
    const LERP_RATE = 0.15;
    for (let i = 0; i < 3; i++) {
      visualAnglesRef.current[i] = THREE.MathUtils.lerp(
        visualAnglesRef.current[i],
        targetAngles[i],
        LERP_RATE
      );
    }

    const [coxaA, femurA, tibiaA] = visualAnglesRef.current;

    if (coxaGroupRef.current)  coxaGroupRef.current.rotation.z  = coxaA;
    if (femurGroupRef.current) femurGroupRef.current.rotation.x  = femurA;
    if (tibiaGroupRef.current) tibiaGroupRef.current.rotation.x  = tibiaA;
  });

  return (
    <group name={`leg-${LEG_NAMES[legIndex]}`}>
      {/* ── Coxa joint sphere ───────────────────────────────── */}
      <mesh material={jointMat} castShadow>
        <sphereGeometry args={[JOINT_R, 8, 8]} />
      </mesh>

      {/* ── Coxa group (rotates Z for horizontal swing) ─────── */}
      <group ref={coxaGroupRef}>
        {/* Coxa segment: offset half-length along X */}
        <mesh
          position={[COXA_LENGTH / 2, 0, 0]}
          material={metalMat}
          castShadow
          receiveShadow
        >
          <boxGeometry args={[COXA_LENGTH, SEG_W, SEG_W]} />
        </mesh>

        {/* Femur joint */}
        <mesh position={[COXA_LENGTH, 0, 0]} material={jointMat} castShadow>
          <sphereGeometry args={[JOINT_R, 8, 8]} />
        </mesh>

        {/* ── Femur group (at end of coxa, rotates X for vertical lift) */}
        <group ref={femurGroupRef} position={[COXA_LENGTH, 0, 0]}>
          <mesh
            position={[0, -FEMUR_LENGTH / 2, 0]}
            material={metalMat}
            castShadow
            receiveShadow
          >
            <boxGeometry args={[SEG_W, FEMUR_LENGTH, SEG_W]} />
          </mesh>

          {/* Tibia joint */}
          <mesh position={[0, -FEMUR_LENGTH, 0]} material={jointMat} castShadow>
            <sphereGeometry args={[JOINT_R, 8, 8]} />
          </mesh>

          {/* ── Tibia group (at end of femur, rotates X for extension) */}
          <group ref={tibiaGroupRef} position={[0, -FEMUR_LENGTH, 0]}>
            <mesh
              position={[0, -TIBIA_LENGTH / 2, 0]}
              material={metalMat}
              castShadow
              receiveShadow
            >
              {/* Slightly tapered tibia using scaled box */}
              <boxGeometry args={[SEG_W * 0.75, TIBIA_LENGTH, SEG_W * 0.75]} />
            </mesh>

            {/* Foot sphere */}
            <mesh
              position={[0, -TIBIA_LENGTH, 0]}
              material={inContact ? contactMat : footMat}
              castShadow
            >
              <sphereGeometry args={[JOINT_R * 1.3, 8, 8]} />
            </mesh>

            {/* Axis helper per joint */}
            {showAxes && <axesHelper args={[0.04]} />}
          </group>

          {showAxes && <axesHelper args={[0.04]} />}
        </group>

        {showAxes && <axesHelper args={[0.04]} />}
      </group>

      {/* Overlay: leg name */}
      {showLegName && (
        <mesh position={[COXA_LENGTH * 0.5, 0.02, 0]}>
          {/* Billboard text placeholder — drei <Text> would be used in production */}
        </mesh>
      )}

      {/* Servo number labels */}
      {showNumbers && (
        <>
          {/* Labels would use @react-three/drei Text in production */}
        </>
      )}

      {showFootPosition && (
        <>
          {/* Foot position crosshair — shown as a small ring at foot tip */}
        </>
      )}
    </group>
  );
});

LegAssembly.displayName = 'LegAssembly';
