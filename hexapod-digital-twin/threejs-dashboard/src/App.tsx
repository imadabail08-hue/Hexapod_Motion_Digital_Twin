import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import * as THREE from 'three';

import { HighDetailHexapodModel, LegJoints } from './robot/HighDetailHexapodModel';
import './App.css';

type MotionSource = 'HARDWARE' | 'TRIPOD_GAIT' | 'MANUAL';
type CameraView = 'PERSPECTIVE' | 'TOP' | 'PROFILE';

export const App: React.FC = () => {
  // Motion Source & Control Mode
  const [motionSource, setMotionSource] = useState<MotionSource>('HARDWARE');
  const [stabilisation, setStabilisation] = useState<boolean>(true);
  const [manualRoll, setManualRoll] = useState(0.0);
  const [manualPitch, setManualPitch] = useState(0.0);
  const [invertRoll, setInvertRoll] = useState(false);
  const [invertPitch, setInvertPitch] = useState(false);
  const [bodyHeight, setBodyHeight] = useState(105); // mm

  // Visual options
  const [explodedView, setExplodedView] = useState(false);
  const [wireframe, setWireframe] = useState(false);
  const [cameraView, setCameraView] = useState<CameraView>('PERSPECTIVE');
  const [activeTab, setActiveTab] = useState<'3D' | 'REALTIME' | 'GRAPHS' | 'COMMANDS' | 'SETTINGS'>('3D');

  // Real-Time Attitude (Live Angles)
  const [liveRoll, setLiveRoll] = useState(0.0);
  const [livePitch, setLivePitch] = useState(0.0);
  const [liveYaw, setLiveYaw] = useState(0.0);
  const [physicalServoAngle, setPhysicalServoAngle] = useState(90);

  // Hardware Connection (ESP32 via Serial / WebSocket)
  const [espConnected, setEspConnected] = useState(false);
  const [history, setHistory] = useState<{ t: number; roll: number; pitch: number }[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const hardwarePhaseRef = useRef(0);
  const latestTelemetryRef = useRef({ roll: 0, pitch: 0, yaw: 0, servo: 90 });

  // Orbit controls reference
  const controlsRef = useRef<any>(null);

  // 18 Articulated joint angles for the 6 legs (Neutral Standing Posture)
  // G1=LF, G2=LM, G3=LR, D1=RF, D2=RM, D3=RR
  const [jointAngles, setJointAngles] = useState<{ [key: string]: LegJoints }>({
    G1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    G2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    G3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    D1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    D2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    D3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
  });

  // ──────────────────────────────────────────────────────────────────────────
  // 1. WEBSOCKET HARDWARE TELEMETRY INGESTION (ws://127.0.0.1:8765)
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connectWS = () => {
      try {
        ws = new WebSocket('ws://127.0.0.1:8765');
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[TWIN] Connected to ESP32 Serial WebSocket Gateway!');
          setEspConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.connected !== undefined) {
              setEspConnected(data.connected);
            }
            if (typeof data.roll === 'number') {
              const r = invertRoll ? -data.roll : data.roll;
              const p = invertPitch ? -data.pitch : data.pitch;
              const y = data.yaw || 0.0;
              const s = data.servo !== undefined ? data.servo : 90;

              setLiveRoll(Math.round(r * 10) / 10);
              setLivePitch(Math.round(p * 10) / 10);
              setLiveYaw(Math.round(y * 10) / 10);
              setPhysicalServoAngle(s);

              latestTelemetryRef.current = { roll: r, pitch: p, yaw: y, servo: s };
            }
          } catch (e) {}
        };

        ws.onclose = () => {
          setEspConnected(false);
          retryTimer = setTimeout(connectWS, 1500);
        };

        ws.onerror = () => {
          if (ws) ws.close();
        };
      } catch (e) {
        retryTimer = setTimeout(connectWS, 2000);
      }
    };

    connectWS();

    return () => {
      if (retryTimer) clearTimeout(retryTimer);
      if (ws) ws.close();
    };
  }, [invertRoll, invertPitch, motionSource, stabilisation]);

  // ──────────────────────────────────────────────────────────────────────────
  // 2. SIMULATION & GAIT LOOP (Fallback / Offline Gait Generator)
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    let t = 0;
    const interval = setInterval(() => {
      if (motionSource === 'HARDWARE') {
        const p = latestTelemetryRef.current.pitch;
        const r = latestTelemetryRef.current.roll;

        // TILT-TO-WALK INERTIAL LOCOMOTION
        // Si Pitch > 3° : Marche avant
        // Si Pitch < -3° : Marche arrière
        // Si au repos (|Pitch| <= 3°): Posture neutre fixe sur le plan
        if (Math.abs(p) > 3.0) {
          const speed = (p / 25.0) * 3.8;
          hardwarePhaseRef.current += speed * 0.035;

          const phaseA = Math.sin(hardwarePhaseRef.current);
          const phaseB = Math.sin(hardwarePhaseRef.current + Math.PI);
          const strideAmp = Math.min(Math.max(Math.abs(p) * 0.65, 8), 22);
          const liftAmp = Math.min(Math.max(Math.abs(p) * 0.55, 6), 18);
          const steerAmp = Math.max(Math.min(r * 0.35, 12), -12);

          setJointAngles({
            G1: {
              coxa: Math.round(phaseA * strideAmp + steerAmp),
              femur: Math.round(36 + (phaseA > 0 ? phaseA * liftAmp : 0)),
              tibia: Math.round(82 - (phaseA > 0 ? phaseA * (liftAmp * 0.65) : 0)),
              inContact: phaseA <= 0,
            },
            G2: {
              coxa: Math.round(phaseB * strideAmp - steerAmp),
              femur: Math.round(36 + (phaseB > 0 ? phaseB * liftAmp : 0)),
              tibia: Math.round(82 - (phaseB > 0 ? phaseB * (liftAmp * 0.65) : 0)),
              inContact: phaseB <= 0,
            },
            G3: {
              coxa: Math.round(phaseA * strideAmp + steerAmp),
              femur: Math.round(36 + (phaseA > 0 ? phaseA * liftAmp : 0)),
              tibia: Math.round(82 - (phaseA > 0 ? phaseA * (liftAmp * 0.65) : 0)),
              inContact: phaseA <= 0,
            },
            D1: {
              coxa: Math.round(phaseB * strideAmp + steerAmp),
              femur: Math.round(36 + (phaseB > 0 ? phaseB * liftAmp : 0)),
              tibia: Math.round(82 - (phaseB > 0 ? phaseB * (liftAmp * 0.65) : 0)),
              inContact: phaseB <= 0,
            },
            D2: {
              coxa: Math.round(phaseA * strideAmp - steerAmp),
              femur: Math.round(36 + (phaseA > 0 ? phaseA * liftAmp : 0)),
              tibia: Math.round(82 - (phaseA > 0 ? phaseA * (liftAmp * 0.65) : 0)),
              inContact: phaseA <= 0,
            },
            D3: {
              coxa: Math.round(phaseB * strideAmp + steerAmp),
              femur: Math.round(36 + (phaseB > 0 ? phaseB * liftAmp : 0)),
              tibia: Math.round(82 - (phaseB > 0 ? phaseB * (liftAmp * 0.65) : 0)),
              inContact: phaseB <= 0,
            },
          });
        } else {
          // État initial neutre : Robot parfaitement fixe sur le plan
          setJointAngles({
            G1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
            G2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
            G3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
            D1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
            D2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
            D3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
          });
        }
      } else if (motionSource === 'TRIPOD_GAIT') {
        const phaseA = Math.sin(t * 3.2);
        const phaseB = Math.sin(t * 3.2 + Math.PI);

        // Body heave and pitch during gait
        setLiveRoll(Math.round(Math.sin(t * 3.2) * 3.0 * 10) / 10);
        setLivePitch(Math.round(Math.cos(t * 3.2) * 1.8 * 10) / 10);

        setJointAngles({
          G1: {
            coxa: Math.round(phaseA * 16),
            femur: Math.round(36 + (phaseA > 0 ? phaseA * 16 : 0)),
            tibia: Math.round(82 - (phaseA > 0 ? phaseA * 12 : 0)),
            inContact: phaseA <= 0,
          },
          G2: {
            coxa: Math.round(phaseB * 16),
            femur: Math.round(36 + (phaseB > 0 ? phaseB * 16 : 0)),
            tibia: Math.round(82 - (phaseB > 0 ? phaseB * 12 : 0)),
            inContact: phaseB <= 0,
          },
          G3: {
            coxa: Math.round(phaseA * 16),
            femur: Math.round(36 + (phaseA > 0 ? phaseA * 16 : 0)),
            tibia: Math.round(82 - (phaseA > 0 ? phaseA * 12 : 0)),
            inContact: phaseA <= 0,
          },
          D1: {
            coxa: Math.round(phaseB * 16),
            femur: Math.round(36 + (phaseB > 0 ? phaseB * 16 : 0)),
            tibia: Math.round(82 - (phaseB > 0 ? phaseB * 12 : 0)),
            inContact: phaseB <= 0,
          },
          D2: {
            coxa: Math.round(phaseA * 16),
            femur: Math.round(36 + (phaseA > 0 ? phaseA * 16 : 0)),
            tibia: Math.round(82 - (phaseA > 0 ? phaseA * 12 : 0)),
            inContact: phaseA <= 0,
          },
          D3: {
            coxa: Math.round(phaseB * 16),
            femur: Math.round(36 + (phaseB > 0 ? phaseB * 16 : 0)),
            tibia: Math.round(82 - (phaseB > 0 ? phaseB * 12 : 0)),
            inContact: phaseB <= 0,
          },
        });
      } else if (motionSource === 'MANUAL') {
        const effRoll = invertRoll ? -manualRoll : manualRoll;
        const effPitch = invertPitch ? -manualPitch : manualPitch;
        setLiveRoll(effRoll);
        setLivePitch(effPitch);

        if (stabilisation) {
          const dRoll = effRoll * 0.45;
          const dPitch = effPitch * 0.45;
          setJointAngles({
            G1: { coxa: 0, femur: Math.round(36 + dRoll - dPitch), tibia: 82, inContact: true },
            G2: { coxa: 0, femur: Math.round(36 + dRoll),          tibia: 82, inContact: true },
            G3: { coxa: 0, femur: Math.round(36 + dRoll + dPitch), tibia: 82, inContact: true },
            D1: { coxa: 0, femur: Math.round(36 - dRoll - dPitch), tibia: 82, inContact: true },
            D2: { coxa: 0, femur: Math.round(36 - dRoll),          tibia: 82, inContact: true },
            D3: { coxa: 0, femur: Math.round(36 - dRoll + dPitch), tibia: 82, inContact: true },
          });
        }
      }

      // Sparkline history
      setHistory((prev) => {
        const next = [...prev, { t: Math.round(t * 100) / 100, roll: liveRoll, pitch: livePitch }];
        return next.length > 70 ? next.slice(1) : next;
      });
    }, 30);

    return () => clearInterval(interval);
  }, [motionSource, manualRoll, manualPitch, invertRoll, invertPitch, stabilisation, liveRoll, livePitch]);

  // Camera views
  const handleCameraChange = (view: CameraView) => {
    setCameraView(view);
    if (!controlsRef.current) return;
    if (view === 'TOP') {
      controlsRef.current.object.position.set(0, 0.72, 0.001);
      controlsRef.current.target.set(0, 0.1, 0);
    } else if (view === 'PROFILE') {
      controlsRef.current.object.position.set(0.68, 0.15, 0);
      controlsRef.current.target.set(0, 0.1, 0);
    } else {
      controlsRef.current.object.position.set(0.44, 0.34, 0.44);
      controlsRef.current.target.set(0, 0.1, 0);
    }
    controlsRef.current.update();
  };

  const resetNeutral = () => {
    setManualRoll(0.0);
    setManualPitch(0.0);
    setBodyHeight(105);
    setJointAngles({
      G1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
      G2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
      G3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
      D1: { coxa: 0, femur: 36, tibia: 82, inContact: true },
      D2: { coxa: 0, femur: 36, tibia: 82, inContact: true },
      D3: { coxa: 0, femur: 36, tibia: 82, inContact: true },
    });
  };

  return (
    <div className="hexa-app-root">
      {/* ================================================================== */}
      {/* TOP HEADER                                                         */}
      {/* ================================================================== */}
      <header className="hexa-header">
        <div className="header-left">
          <div className="logo-badge">
            <span className="logo-hex-icon">⬡</span>
            <div className="logo-text-block">
              <span className="logo-title">HEXA</span>
              <span className="logo-subtitle">MOTION DIGITAL TWIN</span>
            </div>
          </div>
          <span className="header-divider">/</span>
          <span className="header-breadcrumb">HEX-01 · ESP32 + MPU6050 (0x69) · 18 DDL</span>
        </div>

        <div className="header-right">
          <div className={`status-pill ${espConnected ? 'online' : 'offline'}`}>
            <span className="status-dot">●</span>
            <span>{espConnected ? 'MPU Connecté (COM8 · 50Hz)' : 'Recherche ESP32 (COM8)...'}</span>
          </div>
        </div>
      </header>

      {/* ================================================================== */}
      {/* MAIN WORKSPACE                                                     */}
      {/* ================================================================== */}
      <main className="hexa-main-body">
        {/* ---------------------------------------------------------------- */}
        {/* LEFT COLUMN: GAUGES & CONTROLS (MATCHING POSTER SECTION 5)        */}
        {/* ---------------------------------------------------------------- */}
        <aside className="hexa-left-sidebar">
          <div className="sidebar-section-title">ORIENTATION EN TEMPS RÉEL</div>

          {/* 3 CIRCULAR RADIAL GAUGES (MATCHING POSTER) */}
          <div className="poster-gauges-container">
            {/* ROLL GAUGE */}
            <div className="gauge-card">
              <div className="gauge-header">
                <span className="gauge-label">ROLL</span>
                <span className="gauge-unit">AXE X</span>
              </div>
              <div className="gauge-dial">
                <svg viewBox="0 0 100 60" className="gauge-svg">
                  <path d="M 15 50 A 35 35 0 0 1 85 50" fill="none" stroke="#1e293b" strokeWidth="8" strokeLinecap="round" />
                  <path
                    d="M 15 50 A 35 35 0 0 1 85 50"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="110"
                    strokeDashoffset={Math.max(0, Math.min(110, 55 - (liveRoll / 40) * 55))}
                  />
                </svg>
                <div className="gauge-value green">{liveRoll.toFixed(1)}°</div>
              </div>
            </div>

            {/* PITCH GAUGE */}
            <div className="gauge-card">
              <div className="gauge-header">
                <span className="gauge-label">PITCH</span>
                <span className="gauge-unit">AXE Y</span>
              </div>
              <div className="gauge-dial">
                <svg viewBox="0 0 100 60" className="gauge-svg">
                  <path d="M 15 50 A 35 35 0 0 1 85 50" fill="none" stroke="#1e293b" strokeWidth="8" strokeLinecap="round" />
                  <path
                    d="M 15 50 A 35 35 0 0 1 85 50"
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="110"
                    strokeDashoffset={Math.max(0, Math.min(110, 55 - (livePitch / 40) * 55))}
                  />
                </svg>
                <div className="gauge-value orange">{livePitch.toFixed(1)}°</div>
              </div>
            </div>

            {/* YAW GAUGE */}
            <div className="gauge-card">
              <div className="gauge-header">
                <span className="gauge-label">YAW</span>
                <span className="gauge-unit">AXE Z (EST.)</span>
              </div>
              <div className="gauge-dial">
                <svg viewBox="0 0 100 60" className="gauge-svg">
                  <path d="M 15 50 A 35 35 0 0 1 85 50" fill="none" stroke="#1e293b" strokeWidth="8" strokeLinecap="round" />
                  <path
                    d="M 15 50 A 35 35 0 0 1 85 50"
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="110"
                    strokeDashoffset={Math.max(0, Math.min(110, 55 - (liveYaw / 180) * 55))}
                  />
                </svg>
                <div className="gauge-value cyan">{liveYaw.toFixed(1)}°</div>
              </div>
            </div>
          </div>

          {/* MODE SELECTOR */}
          <div className="control-group" style={{ marginTop: '16px' }}>
            <div className="group-header">
              <span>Source de mouvement</span>
              <span className={`badge-mode-pill ${espConnected ? 'live' : ''}`}>
                {espConnected ? 'ESP32 DIRECT' : 'LOCAL'}
              </span>
            </div>
            <div className="btn-segmented">
              <button
                className={`seg-btn ${motionSource === 'HARDWARE' ? 'active' : ''}`}
                onClick={() => setMotionSource('HARDWARE')}
              >
                Matériel Live
              </button>
              <button
                className={`seg-btn ${motionSource === 'TRIPOD_GAIT' ? 'active' : ''}`}
                onClick={() => setMotionSource('TRIPOD_GAIT')}
              >
                Marche Tripode
              </button>
              <button
                className={`seg-btn ${motionSource === 'MANUAL' ? 'active' : ''}`}
                onClick={() => setMotionSource('MANUAL')}
              >
                Manuel
              </button>
            </div>
          </div>

          {/* STABILISATION TOGGLE (POSTER SECTION 5) */}
          <div className="control-group">
            <div className="stabilisation-row">
              <div>
                <div className="stab-title">Stabilisation Active</div>
                <div className="stab-subtitle">Asservissement postural IMU</div>
              </div>
              <button
                className={`toggle-switch ${stabilisation ? 'active' : ''}`}
                onClick={() => setStabilisation(!stabilisation)}
              >
                {stabilisation ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>

          {/* MANUAL SLIDERS (IF IN MANUAL MODE) */}
          {motionSource === 'MANUAL' && (
            <div className="control-group">
              <div className="group-header">
                <span>Contrôles Manuels</span>
                <button className="btn-link" onClick={resetNeutral}>Reset</button>
              </div>

              <div className="slider-row">
                <div className="slider-labels">
                  <span>Roll</span>
                  <span className="slider-val red">{manualRoll.toFixed(1)}°</span>
                </div>
                <input
                  type="range"
                  min="-35"
                  max="35"
                  step="0.5"
                  value={manualRoll}
                  onChange={(e) => setManualRoll(parseFloat(e.target.value))}
                />
              </div>

              <div className="slider-row">
                <div className="slider-labels">
                  <span>Pitch</span>
                  <span className="slider-val green">{manualPitch.toFixed(1)}°</span>
                </div>
                <input
                  type="range"
                  min="-35"
                  max="35"
                  step="0.5"
                  value={manualPitch}
                  onChange={(e) => setManualPitch(parseFloat(e.target.value))}
                />
              </div>

              <div className="checkbox-row" style={{ marginTop: '10px', display: 'flex', gap: '12px', fontSize: '11px', color: '#94a3b8' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={invertRoll}
                    onChange={(e) => setInvertRoll(e.target.checked)}
                  />
                  Inverser Roll
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={invertPitch}
                    onChange={(e) => setInvertPitch(e.target.checked)}
                  />
                  Inverser Pitch
                </label>
              </div>
            </div>
          )}

          {/* PHYSICAL MG90S SERVO CARD */}
          <div className="servo-physical-badge">
            <div className="servo-phys-title">Servo Physique MG90S (GPIO 19)</div>
            <div className="servo-phys-val">{physicalServoAngle}°</div>
            <div className="servo-phys-bar">
              <div
                className="servo-phys-fill"
                style={{ width: `${((physicalServoAngle - 50) / 80) * 100}%` }}
              />
            </div>
          </div>
        </aside>

        {/* ---------------------------------------------------------------- */}
        {/* CENTER COLUMN: 3D VIEWPORT WITH STUDIO LIGHTING                  */}
        {/* ---------------------------------------------------------------- */}
        <section className="hexa-center-content">
          <div className="scene-card">
            {/* Top Scene Controls Bar */}
            <div className="scene-card-header">
              <div className="scene-title-block">
                <span className="scene-sub">VUE NUMÉRIQUE HAUTE FIDÉLITÉ</span>
                <span className="scene-main">HEX-01 · <strong>POSTURE STABLE</strong></span>
              </div>

              <div className="camera-btn-group">
                <button
                  className={`cam-btn ${cameraView === 'PERSPECTIVE' ? 'active' : ''}`}
                  onClick={() => handleCameraChange('PERSPECTIVE')}
                >
                  Perspective
                </button>
                <button
                  className={`cam-btn ${cameraView === 'TOP' ? 'active' : ''}`}
                  onClick={() => handleCameraChange('TOP')}
                >
                  Dessus
                </button>
                <button
                  className={`cam-btn ${cameraView === 'PROFILE' ? 'active' : ''}`}
                  onClick={() => handleCameraChange('PROFILE')}
                >
                  Profil
                </button>
              </div>
            </div>

            {/* Tab Views */}
            {activeTab === 'GRAPHS' ? (
              <div className="tab-panel-container" style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                <h2 style={{ fontSize: '18px', color: '#ffffff', marginBottom: '16px' }}>Oscilloscope Télémétrie Temps Réel (50 Hz)</h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ background: '#0e1625', border: '1px solid #1a273c', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#10b981' }}>ROLL (AXE X)</span>
                      <span style={{ fontFamily: 'monospace', color: '#10b981', fontWeight: 'bold' }}>{liveRoll.toFixed(1)}°</span>
                    </div>
                    <svg width="100%" height="90" preserveAspectRatio="none">
                      <path
                        d={history.length > 1 ? `M 0,45 ` + history.map((pt, idx) => `L ${(idx / (history.length - 1)) * 400},${45 - pt.roll * 1.5}`).join(' ') : 'M 0,45 L 400,45'}
                        fill="none" stroke="#10b981" strokeWidth="2.5"
                      />
                    </svg>
                  </div>
                  <div style={{ background: '#0e1625', border: '1px solid #1a273c', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#f97316' }}>PITCH (AXE Y)</span>
                      <span style={{ fontFamily: 'monospace', color: '#f97316', fontWeight: 'bold' }}>{livePitch.toFixed(1)}°</span>
                    </div>
                    <svg width="100%" height="90" preserveAspectRatio="none">
                      <path
                        d={history.length > 1 ? `M 0,45 ` + history.map((pt, idx) => `L ${(idx / (history.length - 1)) * 400},${45 - pt.pitch * 1.5}`).join(' ') : 'M 0,45 L 400,45'}
                        fill="none" stroke="#f97316" strokeWidth="2.5"
                      />
                    </svg>
                  </div>
                  <div style={{ background: '#0e1625', border: '1px solid #1a273c', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#06b6d4' }}>YAW GYROSCOPIQUE (AXE Z)</span>
                      <span style={{ fontFamily: 'monospace', color: '#06b6d4', fontWeight: 'bold' }}>{liveYaw.toFixed(1)}°</span>
                    </div>
                    <div style={{ height: '90px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '13px' }}>
                      Intégration gyrométrique active · 50 Hz
                    </div>
                  </div>
                  <div style={{ background: '#0e1625', border: '1px solid #1a273c', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>SERVO PHYSIQUE MG90S</span>
                      <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 'bold' }}>{physicalServoAngle}°</span>
                    </div>
                    <div style={{ height: '90px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '8px' }}>
                      <div style={{ width: '100%', height: '12px', background: '#1e293b', borderRadius: '6px', overflow: 'hidden' }}>
                        <div style={{ width: `${((physicalServoAngle - 50) / 80) * 100}%`, height: '100%', background: '#38bdf8' }} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b' }}>
                        <span>50° (Min)</span>
                        <span>90° (Neutre)</span>
                        <span>130° (Max)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : activeTab === 'COMMANDS' ? (
              <div className="tab-panel-container" style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                <h2 style={{ fontSize: '18px', color: '#ffffff', marginBottom: '16px' }}>Panneau de Contrôle & Commandes Robotiques</h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <button className="btn-secondary-full" style={{ padding: '16px', fontSize: '13px', background: '#1e293b' }} onClick={resetNeutral}>
                    🎯 Définir Posture Neutre (Zéro)
                  </button>
                  <button className="btn-secondary-full" style={{ padding: '16px', fontSize: '13px', background: '#065f46' }} onClick={() => setStabilisation(!stabilisation)}>
                    🔄 Basculer Stabilisation IMU ({stabilisation ? 'ACTIVE' : 'OFF'})
                  </button>
                  <button className="btn-secondary-full" style={{ padding: '16px', fontSize: '13px', background: '#1e293b' }} onClick={() => setMotionSource('TRIPOD_GAIT')}>
                    🕷️ Activer Démarche Tripode
                  </button>
                  <button className="btn-secondary-full" style={{ padding: '16px', fontSize: '13px', background: '#7f1d1d', color: '#fca5a5' }} onClick={() => { setMotionSource('MANUAL'); setManualPitch(0); setManualRoll(0); }}>
                    🛑 Arrêt d'Urgence (E-STOP)
                  </button>
                </div>
              </div>
            ) : activeTab === 'SETTINGS' ? (
              <div className="tab-panel-container" style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                <h2 style={{ fontSize: '18px', color: '#ffffff', marginBottom: '16px' }}>Paramètres & Matériel Embarqué</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: '#cbd5e1' }}>
                  <div style={{ background: '#0e1625', padding: '14px', borderRadius: '8px', border: '1px solid #1a273c' }}>
                    <strong>Port Série ESP32 :</strong> COM8 (Détecté automatiquement à 115200 bauds)
                  </div>
                  <div style={{ background: '#0e1625', padding: '14px', borderRadius: '8px', border: '1px solid #1a273c' }}>
                    <strong>Centrale Inertielle :</strong> MPU6050 6 axes (I2C 0x69, SDA=GPIO21, SCL=GPIO22)
                  </div>
                  <div style={{ background: '#0e1625', padding: '14px', borderRadius: '8px', border: '1px solid #1a273c' }}>
                    <strong>Actionneur Physique :</strong> MG90S Positional Servo (Signal = GPIO19, Période = 20ms / 50Hz)
                  </div>
                  <div style={{ background: '#0e1625', padding: '14px', borderRadius: '8px', border: '1px solid #1a273c' }}>
                    <strong>Filtrage Numérique :</strong> Filtre complémentaire (98% Gyroscope + 2% Accéléromètre)
                  </div>
                </div>
              </div>
            ) : (
              /* 3D Canvas Area with Studio PBR Lighting */
              <div className="scene-canvas-container">
                <Canvas
                  shadows
                  camera={{ position: [0.44, 0.34, 0.44], fov: 40 }}
                  gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
                >
                  <color attach="background" args={['#0a0e17']} />

                  {/* Studio Lighting Setup */}
                  <ambientLight intensity={0.9} />
                  <hemisphereLight args={['#e0f2fe', '#0f172a', 1.1]} />

                  {/* Key Light (Casts crisp shadows) */}
                  <directionalLight
                    position={[3.5, 6, 4]}
                    intensity={2.4}
                    castShadow
                    shadow-mapSize-width={2048}
                    shadow-mapSize-height={2048}
                    shadow-bias={-0.0001}
                  />

                  {/* Fill Light (Softens contrast) */}
                  <directionalLight position={[-4, 4, -3]} intensity={1.3} color="#93c5fd" />

                  {/* Rim Accent Light (Pops metallic edges) */}
                  <directionalLight position={[0, 4, -5]} intensity={1.8} color="#38bdf8" />

                  {/* Underglow accent */}
                  <pointLight position={[0, 0.05, 0]} intensity={0.6} color="#ff6000" distance={0.6} />

                  {/* Ground Metric Grid */}
                  <Grid
                    args={[2.4, 2.4]}
                    cellSize={0.04}
                    cellThickness={0.7}
                    cellColor="#1e293b"
                    sectionSize={0.2}
                    sectionThickness={1.2}
                    sectionColor="#3b82f6"
                    fadeDistance={2.8}
                    position={[0, 0, 0]}
                  />

                  <OrbitControls
                    ref={controlsRef}
                    makeDefault
                    enableDamping
                    dampingFactor={0.06}
                    minDistance={0.25}
                    maxDistance={2.2}
                    target={[0, 0.1, 0]}
                  />

                  {/* Upgraded 3D Hexapod Model */}
                  <HighDetailHexapodModel
                    pitch={motionSource === 'HARDWARE' ? 0 : livePitch}
                    roll={motionSource === 'HARDWARE' ? 0 : liveRoll}
                    yaw={motionSource === 'HARDWARE' ? 0 : liveYaw}
                    bodyHeight={bodyHeight}
                    jointAngles={jointAngles}
                    explodedView={explodedView}
                    wireframe={wireframe}
                  />
                </Canvas>

                {/* Overlays */}
                <div className="axis-legend-overlay">
                  <span className="axis-item red">X Avant (Pitch)</span>
                  <span className="axis-item green">Y Gauche (Roll)</span>
                  <span className="axis-item blue">Z Haut (Yaw)</span>
                </div>

                <div className="floating-scene-actions">
                  <button
                    className={`btn-float ${explodedView ? 'active' : ''}`}
                    onClick={() => setExplodedView(!explodedView)}
                  >
                    Vue éclatée
                  </button>
                  <button
                    className={`btn-float ${wireframe ? 'active' : ''}`}
                    onClick={() => setWireframe(!wireframe)}
                  >
                    Filaire
                  </button>
                </div>

                <div className="mouse-instructions-hint">
                  Clic gauche : rotation · Molette : zoom · Clic droit : translation
                </div>
              </div>
            )}

            {/* Sparkline History Footer */}
            <div className="live-chart-footer">
              <div className="chart-footer-header">
                <span>Historique d'attitude IMU (Fenêtre 10s)</span>
                <span className="chart-meta">ROLL (Vert) · PITCH (Orange)</span>
              </div>
              <div className="mini-sparkline-canvas">
                <svg width="100%" height="42" preserveAspectRatio="none">
                  <path
                    d={
                      history.length > 1
                        ? `M 0,21 ` +
                          history
                            .map((pt, idx) => {
                              const x = (idx / (history.length - 1)) * 800;
                              const y = 21 - pt.roll * 0.8;
                              return `L ${x},${y}`;
                            })
                            .join(' ')
                        : 'M 0,21 L 800,21'
                    }
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                  />
                  <path
                    d={
                      history.length > 1
                        ? `M 0,21 ` +
                          history
                            .map((pt, idx) => {
                              const x = (idx / (history.length - 1)) * 800;
                              const y = 21 - pt.pitch * 0.8;
                              return `L ${x},${y}`;
                            })
                            .join(' ')
                        : 'M 0,21 L 800,21'
                    }
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="2"
                  />
                </svg>
              </div>
            </div>
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* RIGHT COLUMN: 18 SERVOS TABLE (MATCHING POSTER SECTION 5)        */}
        {/* ---------------------------------------------------------------- */}
        <aside className="hexa-right-sidebar">
          <div className="articulations-header">
            <div className="art-title-row">
              <span className="sidebar-section-title">Position des Servos</span>
              <span className="badge-ddl">18 DDL</span>
            </div>
            <span className="art-subtitle">Angles articulaires temps réel</span>
          </div>

          {/* 6 LEGS TABLE */}
          <div className="servos-compact-table">
            <div className="table-hdr-row">
              <span>PATTE</span>
              <span>COXA</span>
              <span>FÉMUR</span>
              <span>TIBIA</span>
            </div>

            {[
              { id: 'G1', label: 'LF (G1)', isPhys: false },
              { id: 'G2', label: 'LM (G2)', isPhys: false },
              { id: 'G3', label: 'LR (G3)', isPhys: false },
              { id: 'D1', label: 'RF (D1)', isPhys: false },
              { id: 'D2', label: 'RM (D2)', isPhys: true }, // Physical MG90S POC
              { id: 'D3', label: 'RR (D3)', isPhys: false },
            ].map((leg) => {
              const state = jointAngles[leg.id] || { coxa: 0, femur: 36, tibia: 82 };
              return (
                <div key={leg.id} className={`table-data-row ${leg.isPhys ? 'physical-active' : ''}`}>
                  <span className="leg-label-cell">
                    <span className={`dot-contact ${state.inContact ? 'touch' : 'lift'}`}>●</span>
                    {leg.label}
                  </span>
                  <span className="val-cell">{state.coxa}°</span>
                  <span className="val-cell">{state.femur}°</span>
                  <span className="val-cell">{state.tibia}°</span>
                </div>
              );
            })}
          </div>

          {/* ARCHITECTURE SUMMARY */}
          <div className="arch-summary-card">
            <div className="arch-step">
              <div className="arch-num">01</div>
              <div className="arch-desc">
                <strong>Lecture MPU6050 (0x69)</strong>
                <span>Accéléromètre + Gyroscope 6 axes</span>
              </div>
            </div>
            <div className="arch-step">
              <div className="arch-num">02</div>
              <div className="arch-desc">
                <strong>Fusion Complémentaire 50Hz</strong>
                <span>Filtrage dt temps réel sur ESP32</span>
              </div>
            </div>
            <div className="arch-step">
              <div className="arch-num">03</div>
              <div className="arch-desc">
                <strong>MG90S Positional (GPIO 19)</strong>
                <span>Asservissement stabilisation actif</span>
              </div>
            </div>
          </div>
        </aside>
      </main>

      {/* ================================================================== */}
      {/* BOTTOM NAVIGATION TABS (MATCHING POSTER SECTION 5)                 */}
      {/* ================================================================== */}
      <footer className="hexa-bottom-nav">
        <div className="nav-tabs-group">
          <button
            className={`tab-btn ${activeTab === '3D' ? 'active' : ''}`}
            onClick={() => setActiveTab('3D')}
          >
            Vue 3D
          </button>
          <button
            className={`tab-btn ${activeTab === 'REALTIME' ? 'active' : ''}`}
            onClick={() => setActiveTab('REALTIME')}
          >
            Temps réel
          </button>
          <button
            className={`tab-btn ${activeTab === 'GRAPHS' ? 'active' : ''}`}
            onClick={() => setActiveTab('GRAPHS')}
          >
            Graphiques
          </button>
          <button
            className={`tab-btn ${activeTab === 'COMMANDS' ? 'active' : ''}`}
            onClick={() => setActiveTab('COMMANDS')}
          >
            Commandes
          </button>
          <button
            className={`tab-btn ${activeTab === 'SETTINGS' ? 'active' : ''}`}
            onClick={() => setActiveTab('SETTINGS')}
          >
            Paramètres
          </button>
        </div>
        <div className="nav-meta-info">
          HEXAPOD MOTION DIGITAL TWIN · INDUSTRIE 4.0 · ESP32 + THREE.JS
        </div>
      </footer>
    </div>
  );
};

export default App;
