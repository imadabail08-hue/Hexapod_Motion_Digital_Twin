// ============================================================
// JointConfig.ts — Per-joint visual rotation configuration
// ============================================================
import * as THREE from 'three';
import { JOINT_CONFIGS } from '../types/ServoMap';

const DEG2RAD = Math.PI / 180;

export interface VisualJointConfig {
  rotationAxis: THREE.Vector3;
  direction: 1 | -1;
  visualNeutralOffset: number;  // degrees added before converting to radians
  minAngle: number;
  maxAngle: number;
}

const AXIS_X = new THREE.Vector3(1, 0, 0);
const AXIS_Y = new THREE.Vector3(0, 1, 0);
const AXIS_Z = new THREE.Vector3(0, 0, 1);

function axisVector(axis: 'X' | 'Y' | 'Z'): THREE.Vector3 {
  switch (axis) {
    case 'X': return AXIS_X.clone();
    case 'Y': return AXIS_Y.clone();
    case 'Z': return AXIS_Z.clone();
  }
}

/**
 * Build visual joint configs from the canonical JOINT_CONFIGS table.
 * Each entry maps servo index → VisualJointConfig for use in Three.js.
 */
export const VISUAL_JOINT_CONFIGS: VisualJointConfig[] = JOINT_CONFIGS.map((jc) => ({
  rotationAxis: axisVector(jc.axis),
  direction: jc.direction,
  visualNeutralOffset: jc.neutralOffset,
  minAngle: jc.minAngle,
  maxAngle: jc.maxAngle,
}));

/**
 * Convert a servo command angle (0°–180°) to a Three.js rotation angle (radians)
 * using the per-joint neutral offset and direction sign.
 *
 * Formula:
 *   visualAngle = direction * (commandDeg + neutralOffset)
 *   radians     = visualAngle * DEG2RAD
 */
export function servoAngleToVisualAngle(servoId: number, commandDeg: number): number {
  const cfg = VISUAL_JOINT_CONFIGS[servoId];
  if (!cfg) return 0;
  const visual = cfg.direction * (commandDeg + cfg.visualNeutralOffset);
  return visual * DEG2RAD;
}

/**
 * Clamp a servo command angle to the physical limits for a given servo.
 */
export function clampServoAngle(servoId: number, commandDeg: number): number {
  const cfg = JOINT_CONFIGS[servoId];
  if (!cfg) return commandDeg;
  return Math.max(cfg.minAngle, Math.min(cfg.maxAngle, commandDeg));
}
