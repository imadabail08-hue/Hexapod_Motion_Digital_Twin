// ============================================================
// HexapodModel.tsx — Complete procedural hexapod in R3F
// ============================================================
import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useTwinStore } from '../store/twinStore';
import { LegAssembly } from './LegAssembly';
import { legAttachmentPosition, LEG_ATTACHMENT_ANGLES_RAD } from '../types/ServoMap';

const BODY_RADIUS = 0.18;
const BODY_HEIGHT = 0.045;
const BODY_SEGMENTS = 6;

// Industrial dark metal material for body
const bodyMaterial = new THREE.MeshStandardMaterial({
  color: '#2c2c2c',
  roughness: 0.65,
  metalness: 0.55,
});
const bodyAccentMaterial = new THREE.MeshStandardMaterial({
  color: '#3a3a3a',
  roughness: 0.5,
  metalness: 0.6,
});

// Target quaternion for smooth SLERP
const _targetQuat = new THREE.Quaternion();
const _euler = new THREE.Euler();

export const HexapodModel: React.FC = React.memo(() => {
  const bodyRef  = useRef<THREE.Group>(null);
  const currentQuatRef = useRef(new THREE.Quaternion());

  const twinState  = useTwinStore((s) => s.state);
  const overlays   = useTwinStore((s) => s.overlays);

  const { virtualServos, orientation, footPositions } = twinState;

  useFrame(() => {
    if (!bodyRef.current) return;

    // Build target quaternion from IMU orientation (pitch/roll/yaw in degrees)
    _euler.set(
      THREE.MathUtils.degToRad(orientation.pitch),
      THREE.MathUtils.degToRad(orientation.yaw),
      THREE.MathUtils.degToRad(orientation.roll),
      'XYZ'
    );
    _targetQuat.setFromEuler(_euler);

    // SLERP body orientation — never snap
    currentQuatRef.current.slerp(_targetQuat, 0.1);
    bodyRef.current.quaternion.copy(currentQuatRef.current);
  });

  return (
    <group name="hexapod-root">
      {/* ── Body group ─────────────────────────────────────── */}
      <group ref={bodyRef} name="hexapod-body">
        {/* Main hexagonal body platform */}
        <mesh material={bodyMaterial} castShadow receiveShadow>
          <cylinderGeometry args={[BODY_RADIUS, BODY_RADIUS, BODY_HEIGHT, BODY_SEGMENTS]} />
        </mesh>

        {/* Top accent ring */}
        <mesh
          position={[0, BODY_HEIGHT / 2 + 0.003, 0]}
          material={bodyAccentMaterial}
          castShadow
        >
          <cylinderGeometry
            args={[BODY_RADIUS * 0.95, BODY_RADIUS * 0.95, 0.004, BODY_SEGMENTS]}
          />
        </mesh>

        {/* Centre hub */}
        <mesh position={[0, BODY_HEIGHT / 2 + 0.005, 0]} castShadow>
          <cylinderGeometry args={[0.025, 0.025, 0.01, 12]} />
          <meshStandardMaterial color="#e65100" roughness={0.4} metalness={0.8} />
        </mesh>

        {/* Robot body axes */}
        {overlays.robotAxes && <axesHelper args={[0.25]} />}

        {/* ── Six legs ──────────────────────────────────────── */}
        {Array.from({ length: 6 }, (_, legIndex) => {
          const attachPos = legAttachmentPosition(legIndex);
          const attachAngle = LEG_ATTACHMENT_ANGLES_RAD[legIndex];

          // Per-leg servo indices: legIndex*3 … legIndex*3+2
          const baseIdx = legIndex * 3;
          const servoAngles: [number, number, number] = [
            virtualServos[baseIdx]     ?? 90,
            virtualServos[baseIdx + 1] ?? 90,
            virtualServos[baseIdx + 2] ?? 90,
          ];

          const contact = footPositions[legIndex]?.inContact ?? false;

          return (
            <group
              key={legIndex}
              position={[attachPos.x, 0, attachPos.z]}
              // Rotate leg group so X points outward from body
              rotation={[0, -attachAngle, 0]}
            >
              <LegAssembly
                legIndex={legIndex}
                servoAngles={servoAngles}
                showAxes={overlays.jointAxes}
                showNumbers={overlays.servoNumbers}
                showLegName={overlays.legNames}
                showFootPosition={overlays.footPositions}
                inContact={contact}
              />
            </group>
          );
        })}
      </group>

      {/* World axes helper */}
      {overlays.worldAxes && <axesHelper args={[0.5]} />}
    </group>
  );
});

HexapodModel.displayName = 'HexapodModel';
