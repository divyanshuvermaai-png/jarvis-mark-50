import React, { useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { EffectComposer, Bloom, ChromaticAberration, Noise, Vignette, DepthOfField, ToneMapping } from '@react-three/postprocessing';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import gsap from 'gsap';

import ArcReactor from './ArcReactor';
import ArcEnvironment from './ArcEnvironment';
import ProjectorCone from './ProjectorCone';
import HoloBlueprintRings from './HoloBlueprintRings';
import EnergyArcs from './EnergyArcs';
import EmberTrails from './EmberTrails';
import ScanLaser from './ScanLaser';
import { AudioSync } from '../audio/AudioSync';

export type ReactorSubPhase =
  | 'materialization'
  | 'assembly'
  | 'scanning'
  | 'synchronization'
  | 'activation'
  | 'collapse';

interface ReactorSceneProps {
  phase: ReactorSubPhase;
  audioSync?: AudioSync | null;
  onCollapseComplete?: () => void;
  onLatchSound?: () => void;
  onScanSound?: () => void;
  onSyncSound?: () => void;
  onShockwaveSound?: () => void;
  onRiserSound?: () => void;
}

/**
 * StudioEnvironment injects Three.js's built-in RoomEnvironment into the scene.
 * This provides true PBR environment reflections so brushed aluminum, mirror chrome,
 * glossy copper magnet wire, and clear acrylic refract and gleam realistically.
 */
function StudioEnvironment() {
  const { gl, scene } = useThree();

  useEffect(() => {
    const pmremGenerator = new THREE.PMREMGenerator(gl);
    pmremGenerator.compileEquirectangularShader();
    const roomEnv = new RoomEnvironment();
    const envMap = pmremGenerator.fromScene(roomEnv).texture;
    scene.environment = envMap;

    return () => {
      scene.environment = null;
      envMap.dispose();
      pmremGenerator.dispose();
    };
  }, [gl, scene]);

  return null;
}

function CinematicCamera({ phase }: { phase: ReactorSubPhase }) {
  const { camera } = useThree();
  const phaseRef = useRef(phase);
  const rigRef = useRef({ angle: 0.18, distance: 9.4, height: 1.8 });
  const shakeRef = useRef(0);

  useEffect(() => {
    phaseRef.current = phase;
    if (phase === 'materialization') {
      // Start at dramatic heroic distance, slowly tracking closer
      gsap.fromTo(rigRef.current,
        { distance: 10.8, height: 2.2, angle: 0.35 },
        { distance: 8.8, height: 1.4, angle: 0.12, duration: 15, ease: 'power1.inOut' }
      );
    } else if (phase === 'scanning') {
      // 18.0s beat drop camera jolt and subtle push-in
      shakeRef.current = 0.26;
      gsap.to(rigRef.current, { distance: 8.2, height: 1.1, duration: 0.8, ease: 'power2.out' });
    } else if (phase === 'activation') {
      // Hero close-up showing gleaming copper coils, chrome bolts, and white-hot core filling the frame
      gsap.to(rigRef.current, { distance: 6.8, height: 0.6, duration: 2.2, ease: 'power2.out' });
      setTimeout(() => {
        shakeRef.current = 0.44;
      }, 250);
    } else if (phase === 'collapse') {
      // Pull away smoothly as the reactor collapses into a single quantum point
      gsap.to(rigRef.current, { distance: 13.8, height: 0.0, duration: 2.0, ease: 'power2.in' });
    }
  }, [phase]);

  useFrame((state, delta) => {
    // Subtle orbital camera drift so specular highlights roll across the copper wire coils
    if (phaseRef.current !== 'activation' && phaseRef.current !== 'collapse') {
      rigRef.current.angle += delta * 0.035;
    }

    const baseX = Math.sin(rigRef.current.angle) * rigRef.current.distance;
    const baseZ = Math.cos(rigRef.current.angle) * rigRef.current.distance;
    const baseY = rigRef.current.height;

    // Apply explosive physical camera shake
    let shakeX = 0;
    let shakeY = 0;
    let shakeZ = 0;
    if (shakeRef.current > 0.001) {
      shakeX = (Math.random() - 0.5) * shakeRef.current;
      shakeY = (Math.random() - 0.5) * shakeRef.current;
      shakeZ = (Math.random() - 0.5) * (shakeRef.current * 0.5);
      shakeRef.current = THREE.MathUtils.damp(shakeRef.current, 0, 7.0, delta);
    }

    camera.position.x = baseX + shakeX;
    camera.position.z = baseZ + shakeZ;
    camera.position.y = baseY + shakeY;
    camera.lookAt(0, 0, 0);
  });

  return null;
}

/**
 * Interactive Parallax Rig that tilts the 3D hologram based on mouse position,
 * creating tangible depth of field and multi-layer parallax between coils and core.
 */
function HolographicParallaxRig({ children }: { children: React.ReactNode }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (!groupRef.current) return;
    const targetPitch = -state.pointer.y * 0.22; // ~13 degrees pitch
    const targetYaw = state.pointer.x * 0.32;   // ~18 degrees yaw

    groupRef.current.rotation.x = THREE.MathUtils.damp(
      groupRef.current.rotation.x,
      targetPitch,
      5.0,
      delta
    );
    groupRef.current.rotation.y = THREE.MathUtils.damp(
      groupRef.current.rotation.y,
      targetYaw,
      5.0,
      delta
    );
  });

  return <group ref={groupRef}>{children}</group>;
}

export default function ReactorScene({
  phase,
  audioSync,
  onCollapseComplete,
  onLatchSound,
  onScanSound,
  onSyncSound,
  onShockwaveSound,
  onRiserSound,
}: ReactorSceneProps) {

  // Coordinate sound effects with the physical assembly lifecycle
  useEffect(() => {
    if (phase === 'assembly' && onRiserSound) onRiserSound();
    if (phase === 'scanning' && onScanSound) onScanSound();
    if (phase === 'synchronization' && onSyncSound) onSyncSound();
    if (phase === 'activation' && onShockwaveSound) onShockwaveSound();
  }, [phase, onScanSound, onSyncSound, onShockwaveSound, onRiserSound]);

  // Complete callback on collapse
  useEffect(() => {
    if (phase === 'collapse' && onCollapseComplete) {
      const timer = setTimeout(onCollapseComplete, 2200);
      return () => clearTimeout(timer);
    }
  }, [phase, onCollapseComplete]);

  return (
    <Canvas
      camera={{ position: [0, 1.8, 9.4], fov: 45 }}
      gl={{ alpha: true, antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.15 }}
      style={{ background: 'transparent', width: '100%', height: '100vh' }}
    >
      <Suspense fallback={null}>
        {/* Studio PBR Environment Map for realistic metal and glass reflections */}
        <StudioEnvironment />

        {/* ── Studio 3-Point Lighting Setup for Authentic Prop Realism ── */}
        <ambientLight intensity={0.38} />

        {/* Crisp key light catching copper wire turns, chrome terminals, and aluminum bevels */}
        <directionalLight position={[6, 8, 11]} intensity={3.2} color="#ffffff" />

        {/* Soft cool fill light for underside shadows */}
        <directionalLight position={[-6, -4, 8]} intensity={1.4} color="#0055bb" />

        {/* Electric cyan rim light accentuating the circular outer casing and mounting clamps */}
        <directionalLight position={[-4, 7, -8]} intensity={2.6} color="#00e5ff" />

        <CinematicCamera phase={phase} />

        {/* ── Interactive Holographic Mouse Parallax Rig ── */}
        <HolographicParallaxRig>
          {/* Volumetric Holographic Projection Cone from below */}
          <ProjectorCone phase={phase} />

          {/* Concentric 3D Holographic CAD Reticles & Graduation Blueprint Rings */}
          <HoloBlueprintRings phase={phase} />

          {/* Real Movie-Accurate Iron Man Arc Reactor with Live Audio Reactivity */}
          <ArcReactor phase={phase} audioSync={audioSync} />

          {/* Procedural Electric Lightning / Plasma Discharge Arcs */}
          <EnergyArcs phase={phase} visible={true} intensity={1.3} audioSync={audioSync} />

          {/* 120 Cinematic Ember Spark Trails with Audio-Reactive Bursts */}
          <EmberTrails phase={phase} audioSync={audioSync} />

          {/* Laser Diagnostic Scanning Plane (Divyanshu Industries CAD Mode) */}
          <ScanLaser phase={phase} />

          <ArcEnvironment phase={phase} />
        </HolographicParallaxRig>

        {/* Marvel Studios Cinematic Post-Processing Stack */}
        <EffectComposer enableNormalPass={false}>
          <Bloom
            luminanceThreshold={0.48}
            intensity={phase === 'activation' ? 3.2 : 1.4}
            radius={0.68}
            mipmapBlur
          />
          <ChromaticAberration
            offset={
              phase === 'activation'
                ? new THREE.Vector2(0.004, 0.004)
                : new THREE.Vector2(0.0008, 0.0008)
            }
            radialModulation={true}
            modulationOffset={0.15}
          />
          <Noise
            opacity={0.06}
          />
          <Vignette
            darkness={0.55}
            offset={0.35}
          />
          <ToneMapping />
        </EffectComposer>
      </Suspense>
    </Canvas>
  );
}

