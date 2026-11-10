// ============================================================
// ServoMap.ts — Servo IDs, joint configs, leg/segment metadata
// ============================================================
import * as THREE from 'three';

export enum ServoId {
  LF_COXA   = 0,
  LF_FEMUR  = 1,
  LF_TIBIA  = 2,
  LM_COXA   = 3,
  LM_FEMUR  = 4,
  LM_TIBIA  = 5,
  LR_COXA   = 6,
  LR_FEMUR  = 7,
  LR_TIBIA  = 8,
  RF_COXA   = 9,
  RF_FEMUR  = 10,
  RF_TIBIA  = 11,
  RM_COXA   = 12,
  RM_FEMUR  = 13,
  RM_TIBIA  = 14,
  RR_COXA   = 15,
  RR_FEMUR  = 16,
  RR_TIBIA  = 17,
}

export type LegName = 'LF' | 'LM' | 'LR' | 'RF' | 'RM' | 'RR';
export type SegmentName = 'COXA' | 'FEMUR' | 'TIBIA';

export interface JointConfig {
  name: string;
  axis: 'X' | 'Y' | 'Z';
  direction: 1 | -1;
  neutralOffset: number;   // degrees — added to command angle for visual neutral
  minAngle: number;        // degrees (physical limit)
  maxAngle: number;        // degrees (physical limit)
  leg: LegName;
  segment: SegmentName;
}

// Left-side legs have direction=1 for coxa, right-side direction=-1 (mirror)
export const JOINT_CONFIGS: JointConfig[] = [
  // ── LF ──────────────────────────────────────────────
  { name: 'LF_COXA',  axis: 'Z', direction:  1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'LF', segment: 'COXA'  },
  { name: 'LF_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'LF', segment: 'FEMUR' },
  { name: 'LF_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'LF', segment: 'TIBIA' },
  // ── LM ──────────────────────────────────────────────
  { name: 'LM_COXA',  axis: 'Z', direction:  1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'LM', segment: 'COXA'  },
  { name: 'LM_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'LM', segment: 'FEMUR' },
  { name: 'LM_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'LM', segment: 'TIBIA' },
  // ── LR ──────────────────────────────────────────────
  { name: 'LR_COXA',  axis: 'Z', direction:  1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'LR', segment: 'COXA'  },
  { name: 'LR_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'LR', segment: 'FEMUR' },
  { name: 'LR_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'LR', segment: 'TIBIA' },
  // ── RF ──────────────────────────────────────────────
  { name: 'RF_COXA',  axis: 'Z', direction: -1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'RF', segment: 'COXA'  },
  { name: 'RF_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'RF', segment: 'FEMUR' },
  { name: 'RF_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'RF', segment: 'TIBIA' },
  // ── RM ──────────────────────────────────────────────
  { name: 'RM_COXA',  axis: 'Z', direction: -1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'RM', segment: 'COXA'  },
  { name: 'RM_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'RM', segment: 'FEMUR' },
  { name: 'RM_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'RM', segment: 'TIBIA' },
  // ── RR ──────────────────────────────────────────────
  { name: 'RR_COXA',  axis: 'Z', direction: -1, neutralOffset: -90, minAngle:  45, maxAngle: 135, leg: 'RR', segment: 'COXA'  },
  { name: 'RR_FEMUR', axis: 'X', direction:  1, neutralOffset: -90, minAngle:   0, maxAngle: 180, leg: 'RR', segment: 'FEMUR' },
  { name: 'RR_TIBIA', axis: 'X', direction: -1, neutralOffset:  90, minAngle:   0, maxAngle: 180, leg: 'RR', segment: 'TIBIA' },
] as const;

export const SERVO_NAMES: string[] = JOINT_CONFIGS.map((j) => j.name);

export const LEG_NAMES: LegName[] = ['LF', 'LM', 'LR', 'RF', 'RM', 'RR'];

/** Body attachment angles (radians, around world Y) for each leg */
export const LEG_ATTACHMENT_ANGLES_RAD: number[] = [
  (210 * Math.PI) / 180, // LF
  (270 * Math.PI) / 180, // LM
  (330 * Math.PI) / 180, // LR
  (30  * Math.PI) / 180, // RF
  (90  * Math.PI) / 180, // RM
  (150 * Math.PI) / 180, // RR
];

/** Body radius at which legs attach */
export const BODY_RADIUS = 0.18; // metres

/** Returns the 3D attachment position for a given leg index */
export function legAttachmentPosition(legIndex: number): THREE.Vector3 {
  const angle = LEG_ATTACHMENT_ANGLES_RAD[legIndex];
  return new THREE.Vector3(
    Math.cos(angle) * BODY_RADIUS,
    0,
    Math.sin(angle) * BODY_RADIUS
  );
}
