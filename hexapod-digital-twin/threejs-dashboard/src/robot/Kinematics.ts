// ============================================================
// Kinematics.ts — Forward/inverse kinematics for hexapod legs
// ============================================================

export interface LegDimensions {
  coxaLen: number;   // metres
  femurLen: number;
  tibiaLen: number;
}

export const DEFAULT_LEG_DIMS: LegDimensions = {
  coxaLen:  0.053,
  femurLen: 0.066,
  tibiaLen: 0.090,
};

const DEG2RAD = Math.PI / 180;
const RAD2DEG = 180 / Math.PI;

/** Safe arc-cosine clamped to [-1, 1] to avoid NaN */
export function safeAcos(v: number): number {
  return Math.acos(Math.max(-1, Math.min(1, v)));
}

/**
 * Forward kinematics — servo angles in degrees → foot position (metres)
 * Coordinate system: X forward, Y up, Z right (body frame, per leg)
 * coxaDeg:  horizontal swing (0° = straight forward)
 * femurDeg: vertical lift (90° = horizontal)
 * tibiaDeg: tibia extension (90° = straight)
 */
export function forwardKinematics(
  dims: LegDimensions,
  coxaDeg: number,
  femurDeg: number,
  tibiaDeg: number
): [number, number, number] {
  const coxaRad  = coxaDeg  * DEG2RAD;
  const femurRad = femurDeg * DEG2RAD;
  const tibiaRad = tibiaDeg * DEG2RAD;

  // Project into leg plane
  const coxaX = Math.cos(coxaRad);
  const coxaZ = Math.sin(coxaRad);

  // In leg plane: r is the horizontal distance from coxa joint,
  // h is the vertical distance.
  const legPlaneR =
    dims.coxaLen +
    dims.femurLen * Math.cos(femurRad) +
    dims.tibiaLen * Math.cos(femurRad - tibiaRad);
  const legPlaneY =
    dims.femurLen * Math.sin(femurRad) +
    dims.tibiaLen * Math.sin(femurRad - tibiaRad);

  return [legPlaneR * coxaX, legPlaneY, legPlaneR * coxaZ];
}

/**
 * Inverse kinematics — target position → servo angles in degrees
 * Returns null if the target is unreachable.
 */
export function inverseKinematics(
  dims: LegDimensions,
  targetX: number,
  targetY: number,
  targetZ: number
): [number, number, number] | null {
  const { coxaLen, femurLen, tibiaLen } = dims;

  // Coxa angle
  const coxaDeg = Math.atan2(targetZ, targetX) * RAD2DEG;

  // Distance in leg plane after coxa rotation
  const r = Math.sqrt(targetX * targetX + targetZ * targetZ) - coxaLen;
  const h = targetY;
  const d = Math.sqrt(r * r + h * h);

  // Check reachability
  if (d > femurLen + tibiaLen || d < Math.abs(femurLen - tibiaLen)) {
    return null;
  }

  // Tibia angle (law of cosines)
  const cosAngle2 =
    (femurLen * femurLen + tibiaLen * tibiaLen - d * d) /
    (2 * femurLen * tibiaLen);
  const tibiaDeg = safeAcos(cosAngle2) * RAD2DEG;

  // Femur angle
  const alpha = Math.atan2(h, r) * RAD2DEG;
  const cosAngle1 =
    (femurLen * femurLen + d * d - tibiaLen * tibiaLen) /
    (2 * femurLen * d);
  const beta = safeAcos(cosAngle1) * RAD2DEG;
  const femurDeg = alpha + beta;

  return [coxaDeg, femurDeg, tibiaDeg];
}
