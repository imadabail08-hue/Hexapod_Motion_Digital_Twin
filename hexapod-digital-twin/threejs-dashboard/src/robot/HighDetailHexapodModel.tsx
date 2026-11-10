import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { MG90SServoModel } from './MG90SServoModel';

export interface LegJoints {
  coxa: number;   // degrees (-45 to +45)
  femur: number;  // degrees (0 to 60, higher = higher lift)
  tibia: number;  // degrees (40 to 110, higher = steeper foot)
  inContact?: boolean;
}

interface HighDetailHexapodProps {
  pitch: number;          // degrees
  roll: number;           // degrees
  yaw: number;            // degrees
  bodyHeight: number;     // mm (default 105mm)
  jointAngles: {
    [legId: string]: LegJoints;
  };
  explodedView?: boolean;
  wireframe?: boolean;
}

// 6 Leg Mount Geometry relative to Body Center (60 deg symmetric layout)
// Left side: LF (+45°), LM (+90°), LR (+135°)
// Right side: RF (-45°), RM (-90°), RR (-135°)
const LEG_CONFIGS = [
  { id: 'G1', label: 'LF', angleDeg:  45, mountRadius: 0.088, name: 'Left Front' },
  { id: 'G2', label: 'LM', angleDeg:  90, mountRadius: 0.082, name: 'Left Middle' },
  { id: 'G3', label: 'LR', angleDeg: 135, mountRadius: 0.088, name: 'Left Rear' },
  { id: 'D1', label: 'RF', angleDeg: -45, mountRadius: 0.088, name: 'Right Front' },
  { id: 'D2', label: 'RM', angleDeg: -90, mountRadius: 0.082, name: 'Right Middle' },
  { id: 'D3', label: 'RR', angleDeg:-135, mountRadius: 0.088, name: 'Right Rear' },
];

export const HighDetailHexapodModel: React.FC<HighDetailHexapodProps> = ({
  pitch,
  roll,
  yaw,
  bodyHeight = 105,
  jointAngles,
  explodedView = false,
  wireframe = false,
}) => {
  const rootGroupRef = useRef<THREE.Group>(null);
  const bodyGroupRef = useRef<THREE.Group>(null);

  // High-Grade PBR Materials matching Official Hexapod Poster (Reference B)
  const materials = useMemo(() => {
    return {
      // Carbon / Dark CNC Aluminum Plates
      chassisCarbon: new THREE.MeshStandardMaterial({
        color: '#141822',
        roughness: 0.40,
        metalness: 0.80,
        wireframe,
      }),
      // Center Chassis Ring Accent (Anodized Orange)
      chassisOrangeRing: new THREE.MeshStandardMaterial({
        color: '#ff6200',
        roughness: 0.20,
        metalness: 0.90,
        wireframe,
      }),
      // Anodized Orange Aluminum Links (Brackets, Femur Trusses, Accents)
      anodizedOrange: new THREE.MeshStandardMaterial({
        color: '#ff5e00',
        roughness: 0.22,
        metalness: 0.88,
        wireframe,
      }),
      // Graphite / Dark Carbon Arch Links (Tibia Body)
      graphiteDark: new THREE.MeshStandardMaterial({
        color: '#1a1f28',
        roughness: 0.45,
        metalness: 0.65,
        wireframe,
      }),
      // Machined Stainless Hardware (Standoffs, Pivot Screws)
      machinedMetal: new THREE.MeshStandardMaterial({
        color: '#e2e8f0',
        roughness: 0.16,
        metalness: 0.96,
        wireframe,
      }),
      // High-Grip Rubber Foot Pad
      rubberFoot: new THREE.MeshStandardMaterial({
        color: '#080a0d',
        roughness: 0.95,
        metalness: 0.05,
        wireframe,
      }),
      // ESP32 PCB (Dark FR-4)
      pcbDark: new THREE.MeshStandardMaterial({
        color: '#064e3b',
        roughness: 0.4,
        metalness: 0.3,
        wireframe,
      }),
      // MPU6050 Blue Breakout Board
      mpuBlue: new THREE.MeshStandardMaterial({
        color: '#2563eb',
        roughness: 0.3,
        metalness: 0.35,
        wireframe,
      }),
      // RF Shield Can
      rfShield: new THREE.MeshStandardMaterial({
        color: '#cbd5e1',
        roughness: 0.15,
        metalness: 0.96,
        wireframe,
      }),
      // Foot Ground Contact Rings (Glow Effect on Floor)
      contactGlow: new THREE.MeshBasicMaterial({
        color: '#06b6d4',
        transparent: true,
        opacity: 0.80,
      }),
      contactLift: new THREE.MeshBasicMaterial({
        color: '#64748b',
        transparent: true,
        opacity: 0.20,
      }),
      // Ambient Occlusion Shadow Disc
      shadowOcclusion: new THREE.MeshBasicMaterial({
        color: '#020617',
        transparent: true,
        opacity: 0.65,
      }),
    };
  }, [wireframe]);

  // Smooth interpolation for body attitude (60 FPS)
  useFrame(() => {
    if (bodyGroupRef.current) {
      // Rotation order Z-Y-X: Roll (Z), Pitch (X), Yaw (Y)
      const targetRotX = THREE.MathUtils.degToRad(-pitch);
      const targetRotZ = THREE.MathUtils.degToRad(roll);
      const targetRotY = THREE.MathUtils.degToRad(yaw);

      bodyGroupRef.current.rotation.x = THREE.MathUtils.lerp(
        bodyGroupRef.current.rotation.x,
        targetRotX,
        0.2
      );
      bodyGroupRef.current.rotation.z = THREE.MathUtils.lerp(
        bodyGroupRef.current.rotation.z,
        targetRotZ,
        0.2
      );
      bodyGroupRef.current.rotation.y = THREE.MathUtils.lerp(
        bodyGroupRef.current.rotation.y,
        targetRotY,
        0.2
      );

      // Body height elevation: 105mm default stands firmly above ground
      const targetY = (bodyHeight / 1000.0);
      bodyGroupRef.current.position.y = THREE.MathUtils.lerp(
        bodyGroupRef.current.position.y,
        targetY,
        0.2
      );
    }
  });

  const explodedOffset = explodedView ? 0.035 : 0.0;

  // Compute foot tip coordinates projected onto the ground plane (Y = 0.001)
  const floorContacts = useMemo(() => {
    return LEG_CONFIGS.map((leg) => {
      const mountRad = THREE.MathUtils.degToRad(leg.angleDeg);
      const state = jointAngles[leg.id] || { coxa: 0, femur: 36, tibia: 82, inContact: true };
      const coxaAngleRad = mountRad + THREE.MathUtils.degToRad(state.coxa);

      // Radial reach from center to foot on the ground plane (~0.215m)
      const reach = 0.215;
      const fx = Math.cos(coxaAngleRad) * reach;
      const fz = Math.sin(coxaAngleRad) * reach;

      return {
        id: leg.id,
        x: fx,
        z: fz,
        inContact: state.inContact !== false,
      };
    });
  }, [jointAngles]);

  return (
    <group ref={rootGroupRef} position={[0, 0, 0]}>
      {/* ==================================================================== */}
      {/* GROUND PLANE CONTACT SHADOWS & ANCHOR RINGS (Lying flat on Y = 0.001) */}
      {/* ==================================================================== */}
      {/* Soft Center Chassis Shadow */}
      <mesh position={[0, 0.0005, 0]} rotation={[-Math.PI / 2, 0, 0]} material={materials.shadowOcclusion}>
        <circleGeometry args={[0.18, 32]} />
      </mesh>

      {/* 6 Individual Foot Contact Rings Flat on Floor Grid */}
      {floorContacts.map((contact) => (
        <group key={`floor-${contact.id}`} position={[contact.x, 0.001, contact.z]}>
          {/* Soft Foot Shadow Under Pad */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} material={materials.shadowOcclusion}>
            <circleGeometry args={[0.022, 16]} />
          </mesh>
          {/* Glowing Contact Indicator Ring */}
          <mesh
            rotation={[-Math.PI / 2, 0, 0]}
            material={contact.inContact ? materials.contactGlow : materials.contactLift}
          >
            <ringGeometry args={[0.018, 0.026, 24]} />
          </mesh>
        </group>
      ))}

      {/* ==================================================================== */}
      {/* CENTRAL ROBOT BODY (Elevated in 3D Space)                             */}
      {/* ==================================================================== */}
      <group ref={bodyGroupRef} position={[0, 0.105, 0]}>
        {/* UPPER CHASSIS PLATE (CNC Hexagonal Plate with Circular Cutouts) */}
        <mesh
          position={[0, 0.016 + explodedOffset, 0]}
          material={materials.chassisCarbon}
          castShadow
          receiveShadow
        >
          <cylinderGeometry args={[0.096, 0.096, 0.0035, 6]} />
        </mesh>

        {/* Center Visual Bezel Ring (Anodized Orange Accent) */}
        <mesh
          position={[0, 0.018 + explodedOffset, 0]}
          rotation={[-Math.PI / 2, 0, 0]}
          material={materials.chassisOrangeRing}
        >
          <ringGeometry args={[0.030, 0.036, 32]} />
        </mesh>

        {/* Center Plate Weight-Reduction Cutout / Bay */}
        <mesh position={[0, 0.0175 + explodedOffset, 0]}>
          <cylinderGeometry args={[0.029, 0.029, 0.004, 24]} />
          <meshStandardMaterial color="#0c0e14" roughness={0.9} />
        </mesh>

        {/* LOWER CHASSIS PLATE */}
        <mesh
          position={[0, -0.016 - explodedOffset, 0]}
          material={materials.chassisCarbon}
          castShadow
          receiveShadow
        >
          <cylinderGeometry args={[0.092, 0.092, 0.0035, 6]} />
        </mesh>

        {/* 6 ALUMINUM STANDOFF PILLARS */}
        {[0, 60, 120, 180, 240, 300].map((deg) => {
          const rad = THREE.MathUtils.degToRad(deg);
          const r = 0.068;
          return (
            <mesh
              key={deg}
              position={[r * Math.cos(rad), 0, r * Math.sin(rad)]}
              material={materials.machinedMetal}
              castShadow
            >
              <cylinderGeometry args={[0.003, 0.003, 0.028 + explodedOffset * 2, 8]} />
            </mesh>
          );
        })}

        {/* ELECTRONICS DECK (MakerBoard ESP32 + MPU6050 Breakout) */}
        <group position={[0, 0.020 + explodedOffset * 1.5, 0]}>
          {/* Main ESP32-WROOM Carrier Board */}
          <mesh position={[-0.010, 0.002, 0]} material={materials.pcbDark} castShadow>
            <boxGeometry args={[0.052, 0.002, 0.032]} />
          </mesh>
          {/* ESP32 RF Shield Can */}
          <mesh position={[-0.020, 0.0045, 0]} material={materials.rfShield} castShadow>
            <boxGeometry args={[0.018, 0.003, 0.018]} />
          </mesh>
          {/* Dual Pin Headers */}
          <mesh position={[-0.010, 0.0045, 0.013]} material={materials.machinedMetal}>
            <boxGeometry args={[0.046, 0.0035, 0.0025]} />
          </mesh>
          <mesh position={[-0.010, 0.0045, -0.013]} material={materials.machinedMetal}>
            <boxGeometry args={[0.046, 0.0035, 0.0025]} />
          </mesh>

          {/* MPU6050 IMU Breakout Module (Center Datum) */}
          <group position={[0.018, 0.003, 0]}>
            {/* Blue Module PCB */}
            <mesh material={materials.mpuBlue} castShadow>
              <boxGeometry args={[0.018, 0.0018, 0.022]} />
            </mesh>
            {/* MPU6050 QFN-24 Sensor IC */}
            <mesh position={[0, 0.0015, 0]}>
              <boxGeometry args={[0.005, 0.001, 0.005]} />
              <meshStandardMaterial color="#050505" roughness={0.3} />
            </mesh>
            {/* Decoupling Capacitors */}
            <mesh position={[-0.005, 0.0015, 0.005]}>
              <boxGeometry args={[0.002, 0.001, 0.0015]} />
              <meshStandardMaterial color="#ea580c" roughness={0.4} />
            </mesh>
            {/* IMU Power Indicator LED (Cyan Glow) */}
            <mesh position={[0.005, 0.0018, 0.007]}>
              <sphereGeometry args={[0.0012, 8, 8]} />
              <meshBasicMaterial color="#06b6d4" />
            </mesh>

            {/* IMU Reference Axes (Section 4 du Poster: X Rouge, Y Vert, Z Bleu) */}
            <group position={[0, 0.005, 0]}>
              {/* X Axis (Forward - Red) */}
              <mesh position={[0, 0, 0.008]} rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.0006, 0.0006, 0.016, 8]} />
                <meshBasicMaterial color="#ef4444" />
              </mesh>
              {/* Y Axis (Left - Green) */}
              <mesh position={[-0.008, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
                <cylinderGeometry args={[0.0006, 0.0006, 0.016, 8]} />
                <meshBasicMaterial color="#10b981" />
              </mesh>
              {/* Z Axis (Up - Blue) */}
              <mesh position={[0, 0.008, 0]}>
                <cylinderGeometry args={[0.0006, 0.0006, 0.016, 8]} />
                <meshBasicMaterial color="#3b82f6" />
              </mesh>
            </group>
          </group>
        </group>

        {/* ==================================================================== */}
        {/* 6 INDIVIDUAL ARTICULATED LEGS (CAD FIDELITY & POSTURE)               */}
        {/* ==================================================================== */}
        {LEG_CONFIGS.map((leg) => {
          const mountRad = THREE.MathUtils.degToRad(leg.angleDeg);
          // Default posture: Coxa 0, Femur 36 (pointing UP), Tibia 82 (pointing DOWN)
          const state = jointAngles[leg.id] || { coxa: 0, femur: 36, tibia: 82, inContact: true };

          const coxaRad = THREE.MathUtils.degToRad(state.coxa);
          // Mechanical sign: Negative around X raises the Femur upwards into +Y
          const femurRad = -THREE.MathUtils.degToRad(state.femur);
          // Tibia relative pitch: Positive around X folds the Tibia downwards to ground
          const tibiaRad = THREE.MathUtils.degToRad(state.tibia);

          return (
            <group
              key={leg.id}
              position={[
                leg.mountRadius * Math.cos(mountRad),
                0,
                leg.mountRadius * Math.sin(mountRad),
              ]}
              rotation={[0, -mountRad + Math.PI / 2, 0]}
            >
              {/* ------------------------------------------------------------ */}
              {/* JOINT 1: COXA SERVO (Fixed to Chassis, vertical yaw axis)    */}
              {/* ------------------------------------------------------------ */}
              <group position={[0, -0.004, 0]}>
                <MG90SServoModel
                  rotation={[0, 0, 0]}
                  hornAngleRad={coxaRad}
                  wireframe={wireframe}
                />
              </group>

              {/* ------------------------------------------------------------ */}
              {/* COXA ROTATING ASSEMBLY (Yaw around Y)                        */}
              {/* ------------------------------------------------------------ */}
              <group rotation={[0, coxaRad, 0]}>
                {/* Coxa U-Bracket (Vibrant Anodized Orange Aluminum) */}
                <group position={[0, 0, 0.034 + explodedOffset]}>
                  {/* U-Bracket Main Body */}
                  <mesh material={materials.anodizedOrange} castShadow receiveShadow>
                    <boxGeometry args={[0.024, 0.030, 0.034]} />
                  </mesh>
                  {/* Internal cavity cutout */}
                  <mesh position={[0, 0, 0]} material={materials.graphiteDark}>
                    <boxGeometry args={[0.018, 0.022, 0.022]} />
                  </mesh>

                  {/* -------------------------------------------------------- */}
                  {/* JOINT 2: FEMUR SERVO (Transverse pitch axis)             */}
                  {/* -------------------------------------------------------- */}
                  <group position={[0, 0, 0.008]} rotation={[Math.PI / 2, 0, 0]}>
                    <MG90SServoModel
                      rotation={[0, 0, 0]}
                      hornAngleRad={femurRad}
                      wireframe={wireframe}
                    />
                  </group>

                  {/* -------------------------------------------------------- */}
                  {/* FEMUR ROTATING ASSEMBLY (Pitch around X - ANGLED UP!)     */}
                  {/* -------------------------------------------------------- */}
                  <group position={[0, 0, 0.018]} rotation={[femurRad, 0, 0]}>
                    {/* Metallic Pivot Bearing Pin */}
                    <mesh rotation={[0, 0, Math.PI / 2]} material={materials.machinedMetal}>
                      <cylinderGeometry args={[0.006, 0.006, 0.026, 16]} />
                    </mesh>

                    {/* Femur Dual Skeletonized Truss Arm */}
                    <group position={[0, 0, 0.036 + explodedOffset]}>
                      {/* Left Truss Plate (Anodized Orange) */}
                      <mesh position={[-0.011, 0, 0]} material={materials.anodizedOrange} castShadow>
                        <boxGeometry args={[0.003, 0.024, 0.072]} />
                      </mesh>
                      {/* Right Truss Plate (Anodized Orange) */}
                      <mesh position={[0.011, 0, 0]} material={materials.anodizedOrange} castShadow>
                        <boxGeometry args={[0.003, 0.024, 0.072]} />
                      </mesh>
                      {/* Center Structural Stiffener */}
                      <mesh position={[0, 0, 0]} material={materials.graphiteDark} castShadow>
                        <boxGeometry args={[0.018, 0.016, 0.036]} />
                      </mesh>
                      {/* Truss Circular Weight-Reduction Holes */}
                      <mesh position={[-0.012, 0, -0.012]} material={materials.machinedMetal}>
                        <cylinderGeometry args={[0.004, 0.004, 0.004, 12]} />
                      </mesh>
                      <mesh position={[0.012, 0, -0.012]} material={materials.machinedMetal}>
                        <cylinderGeometry args={[0.004, 0.004, 0.004, 12]} />
                      </mesh>

                      {/* ---------------------------------------------------- */}
                      {/* JOINT 3: TIBIA SERVO (Mounted at Femur distal end)   */}
                      {/* ---------------------------------------------------- */}
                      <group position={[0, -0.002, 0.032]} rotation={[Math.PI / 2, 0, 0]}>
                        <MG90SServoModel
                          rotation={[0, 0, 0]}
                          hornAngleRad={tibiaRad}
                          wireframe={wireframe}
                        />
                      </group>

                      {/* ---------------------------------------------------- */}
                      {/* TIBIA ROTATING ASSEMBLY (Folds DOWNWARDS to floor)   */}
                      {/* ---------------------------------------------------- */}
                      <group position={[0, 0, 0.036]} rotation={[tibiaRad, 0, 0]}>
                        {/* Knee Joint Bearing Pin */}
                        <mesh rotation={[0, 0, Math.PI / 2]} material={materials.machinedMetal}>
                          <cylinderGeometry args={[0.0055, 0.0055, 0.026, 16]} />
                        </mesh>

                        {/* Tibia Knee Upper Bracket (Anodized Orange) */}
                        <mesh position={[0, 0, 0.010]} material={materials.anodizedOrange} castShadow>
                          <boxGeometry args={[0.022, 0.024, 0.022]} />
                        </mesh>

                        {/* Tibia Curved Arched Leg Link */}
                        <group position={[0, 0, 0.052]}>
                          {/* Main Arched Graphite Beam */}
                          <mesh material={materials.graphiteDark} castShadow receiveShadow>
                            <boxGeometry args={[0.014, 0.016, 0.102]} />
                          </mesh>
                          {/* Anodized Orange Side Flanges */}
                          <mesh position={[-0.008, 0, 0]} material={materials.anodizedOrange} castShadow>
                            <boxGeometry args={[0.002, 0.018, 0.098]} />
                          </mesh>
                          <mesh position={[0.008, 0, 0]} material={materials.anodizedOrange} castShadow>
                            <boxGeometry args={[0.002, 0.018, 0.098]} />
                          </mesh>

                          {/* ------------------------------------------------ */}
                          {/* TIBIA GROUND CONTACT FOOT (Rubber hemisphere)   */}
                          {/* ------------------------------------------------ */}
                          <group position={[0, 0, 0.054]}>
                            {/* Machined Metal Foot Retaining Ferrule */}
                            <mesh material={materials.machinedMetal}>
                              <cylinderGeometry args={[0.007, 0.008, 0.008, 16]} />
                            </mesh>
                            {/* Hemispherical Rubber Contact Foot Pad */}
                            <mesh position={[0, 0, 0.005]} material={materials.rubberFoot} castShadow receiveShadow>
                              <sphereGeometry args={[0.012, 20, 20]} />
                            </mesh>
                          </group>
                        </group>
                      </group>
                    </group>
                  </group>
                </group>
              </group>
            </group>
          );
        })}
      </group>
    </group>
  );
};

