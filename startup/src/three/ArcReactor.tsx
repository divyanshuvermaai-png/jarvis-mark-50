import React, { useRef, useEffect, useMemo, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { ReactorSubPhase } from './ReactorScene';
import { AudioSync } from '../audio/AudioSync';

interface ArcReactorProps {
  phase: ReactorSubPhase;
  audioSync?: AudioSync | null;
}

export default function ArcReactor({ phase, audioSync }: ArcReactorProps) {
  const pointLightRef = useRef<THREE.PointLight>(null);
  const coreLightRef = useRef<THREE.PointLight>(null);
  const acrylicGlowRef = useRef<THREE.PointLight>(null);

  // Structural groups corresponding to the real Iron Man Arc Reactor prop
  const coreAssemblyRef = useRef<THREE.Group>(null);
  const statorSpokesRef = useRef<THREE.Group>(null);
  const acrylicRingRef = useRef<THREE.Group>(null);
  const solenoidRingRef = useRef<THREE.Group>(null);
  const outerBezelRef = useRef<THREE.Group>(null);
  const shockwaveRef = useRef<THREE.Mesh>(null);
  const coreParticlesRef = useRef<THREE.Points>(null);
  const dustMotesRef = useRef<THREE.Points>(null);

  // Dynamic copper emissive intensity for audio beats
  const [copperGlow, setCopperGlow] = useState(0.25);

  // 60 Volumetric Holographic Dust Motes drifting through the beam volume
  const dustMotesData = useMemo(() => {
    const count = 60;
    const pos = new Float32Array(count * 3);
    const speed = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 0.5 + Math.random() * 3.4;
      const th = Math.random() * Math.PI * 2;
      pos[i * 3] = Math.cos(th) * r;
      pos[i * 3 + 1] = Math.sin(th) * r;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 2.2;
      speed[i * 3] = (Math.random() - 0.5) * 0.02;
      speed[i * 3 + 1] = 0.02 + Math.random() * 0.04;
      speed[i * 3 + 2] = (Math.random() - 0.5) * 0.02;
    }
    return { pos, speed, count };
  }, []);

  // 28 Quantum Core Orbiting Sparks inside the center
  const particleData = useMemo(() => {
    const count = 28;
    const pos = new Float32Array(count * 3);
    const rad = new Float32Array(count);
    const speed = new Float32Array(count);
    const theta = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      rad[i] = 0.2 + Math.random() * 0.38;
      theta[i] = Math.random() * Math.PI * 2;
      speed[i] = (Math.random() * 0.8 + 0.4) * (Math.random() > 0.5 ? 1 : -1);
      pos[i * 3] = Math.cos(theta[i]) * rad[i];
      pos[i * 3 + 1] = Math.sin(theta[i]) * rad[i];
      pos[i * 3 + 2] = (Math.random() - 0.5) * 0.25;
    }
    return { pos, rad, speed, theta, count };
  }, []);

  // ── GSAP Beat-Synced Lifecycle ──
  useEffect(() => {
    if (phase === 'materialization') {
      // Audio 11.8s - 14.25s: Singularity point ignites, acrylic foundation & outer aluminum collar appear
      if (coreAssemblyRef.current) {
        gsap.fromTo(coreAssemblyRef.current.scale,
          { x: 0.15, y: 0.15, z: 0.15 },
          { x: 0.9, y: 0.9, z: 0.9, duration: 2.2, ease: 'power2.out' }
        );
      }
      if (outerBezelRef.current) {
        gsap.fromTo(outerBezelRef.current.scale,
          { x: 0.3, y: 0.3, z: 0.3 },
          { x: 1.0, y: 1.0, z: 1.0, duration: 2.4, ease: 'power2.out', delay: 0.2 }
        );
      }
      if (acrylicRingRef.current) {
        gsap.fromTo(acrylicRingRef.current.scale,
          { x: 0.2, y: 0.2, z: 0.2 },
          { x: 1.0, y: 1.0, z: 1.0, duration: 2.2, ease: 'power2.out', delay: 0.3 }
        );
      }
      if (pointLightRef.current && coreLightRef.current) {
        gsap.to(pointLightRef.current, { intensity: 4.5, duration: 1.8 });
        gsap.to(coreLightRef.current, { intensity: 5.5, duration: 1.8 });
      }
      if (acrylicGlowRef.current) {
        gsap.to(acrylicGlowRef.current, { intensity: 3.0, duration: 2.0 });
      }
    } else if (phase === 'assembly') {
      // Audio 14.25s: BEAT 1 IMPACT -> 10 Radial CNC Aluminum Spokes lock in
      const tl = gsap.timeline();

      if (coreAssemblyRef.current) {
        tl.to(coreAssemblyRef.current.scale, { x: 1.0, y: 1.0, z: 1.0, duration: 1.2 }, 0);
      }

      if (statorSpokesRef.current) {
        tl.fromTo(statorSpokesRef.current.scale,
          { x: 0.1, y: 0.1, z: 0.1 },
          { x: 1.0, y: 1.0, z: 1.0, duration: 1.4, ease: 'back.out(1.25)' },
          0
        );
      }

      // Audio 18.0s: MASSIVE BEAT DROP -> 10 Copper-Wound Solenoids slam into position!
      if (solenoidRingRef.current) {
        tl.fromTo(solenoidRingRef.current.scale,
          { x: 0.1, y: 0.1, z: 0.1 },
          { x: 1.0, y: 1.0, z: 1.0, duration: 1.4, ease: 'power3.out' },
          3.75
        );
      }

      // Beat drop shockwave expansion
      if (shockwaveRef.current) {
        tl.fromTo(shockwaveRef.current.scale,
          { x: 0.2, y: 0.2, z: 0.2 },
          { x: 4.8, y: 4.8, z: 1.0, duration: 1.2, ease: 'power2.out' },
          3.75
        );
      }

      // Copper glow surge on assembly
      tl.add(() => setCopperGlow(0.6), 3.75);
      tl.add(() => setCopperGlow(0.35), 4.8);
    } else if (phase === 'scanning' || phase === 'synchronization') {
      // Ensure all elements fully constructed
      [coreAssemblyRef.current, statorSpokesRef.current, acrylicRingRef.current, solenoidRingRef.current, outerBezelRef.current].forEach(ref => {
        if (ref) gsap.to(ref.scale, { x: 1.0, y: 1.0, z: 1.0, duration: 0.8 });
      });
      if (pointLightRef.current) gsap.to(pointLightRef.current, { intensity: 11.0, duration: 0.8 });
      if (acrylicGlowRef.current) gsap.to(acrylicGlowRef.current, { intensity: 5.0, duration: 0.8 });
      setCopperGlow(0.45);
    } else if (phase === 'activation') {
      // Audio 30.25s: THE CLIMAX ACTIVATION IMPACT!
      const tl = gsap.timeline();
      if (pointLightRef.current && coreLightRef.current && acrylicGlowRef.current) {
        tl.to([pointLightRef.current, coreLightRef.current, acrylicGlowRef.current], { intensity: 2.0, duration: 0.25 }) // Micro-stillness
          .to(pointLightRef.current, { intensity: 38.0, duration: 0.12 }) // Blinding white-hot arc flash
          .to(coreLightRef.current, { intensity: 26.0, duration: 0.12 }, '<')
          .to(acrylicGlowRef.current, { intensity: 14.0, duration: 0.12 }, '<')
          .to(pointLightRef.current, { intensity: 13.0, duration: 1.8, ease: 'power2.out' }) // Stabilized
          .to(coreLightRef.current, { intensity: 9.5, duration: 1.8, ease: 'power2.out' }, '<')
          .to(acrylicGlowRef.current, { intensity: 6.0, duration: 1.8, ease: 'power2.out' }, '<');
      }

      if (shockwaveRef.current) {
        tl.fromTo(shockwaveRef.current.scale,
          { x: 0.1, y: 0.1, z: 0.1 },
          { x: 5.8, y: 5.8, z: 1.0, duration: 1.4, ease: 'power2.out' },
          0.25
        );
      }
      setCopperGlow(1.0);
    } else if (phase === 'collapse') {
      // Audio 32.6s - 34.4s: Graceful collapse into quantum singularity
      const tl = gsap.timeline();
      const assemblies = [
        outerBezelRef.current,
        solenoidRingRef.current,
        acrylicRingRef.current,
        statorSpokesRef.current,
        coreAssemblyRef.current
      ].filter(Boolean) as THREE.Group[];

      tl.to(assemblies.map(el => el.scale), {
        x: 0.001, y: 0.001, z: 0.001,
        duration: 1.8,
        ease: 'power3.inOut',
        stagger: 0.06
      });

      if (pointLightRef.current && coreLightRef.current) {
        tl.to([pointLightRef.current, coreLightRef.current], { intensity: 0, duration: 1.5 }, 0.6);
      }
    }
  }, [phase]);

  // ── Rotational Dynamics & Internal Particles ──
  useFrame((state) => {
    const t = state.clock.elapsedTime;

    // Heavy, engineered mechanical motion:
    // Outer aluminum chassis is rock-solid (micro-vibration only)
    if (outerBezelRef.current) {
      outerBezelRef.current.rotation.z = Math.sin(t * 0.05) * 0.004;
    }
    // Acrylic ring and copper solenoids slowly track electromagnetic torque
    if (acrylicRingRef.current) {
      acrylicRingRef.current.rotation.z = t * 0.018;
    }
    if (solenoidRingRef.current) {
      solenoidRingRef.current.rotation.z = -t * 0.014;
    }
    // Stator spokes stay firmly anchored
    if (statorSpokesRef.current) {
      statorSpokesRef.current.rotation.z = t * 0.005;
    }

    // Central cathode aperture ring spins fast with vibranium energy
    if (coreAssemblyRef.current) {
      const cathodeRing = coreAssemblyRef.current.children[2] as THREE.Mesh;
      if (cathodeRing) cathodeRing.rotation.z = t * 0.35;
    }

    // Circulate 28 internal quantum sparks
    if (coreParticlesRef.current) {
      const posAttr = coreParticlesRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const array = posAttr.array as Float32Array;
      const { count, rad, speed, theta } = particleData;

      for (let i = 0; i < count; i++) {
        theta[i] += speed[i] * 0.045;
        array[i * 3] = Math.cos(theta[i]) * rad[i];
        array[i * 3 + 1] = Math.sin(theta[i]) * rad[i];
      }
      posAttr.needsUpdate = true;
    }

    // Drift 60 Volumetric Holographic Dust Motes through beam volume
    if (dustMotesRef.current) {
      const posAttr = dustMotesRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const array = posAttr.array as Float32Array;
      const { count, speed } = dustMotesData;

      for (let i = 0; i < count; i++) {
        array[i * 3 + 1] += speed[i * 3 + 1] * 0.06;
        if (array[i * 3 + 1] > 3.2) array[i * 3 + 1] = -3.2;
      }
      posAttr.needsUpdate = true;
    }

    // ── Live 60-FPS Audio-Reactive Waveform Dynamics ──
    if (audioSync) {
      const energy = audioSync.getEnergy();
      // Bass punch drives the central core scale dynamically
      if (coreAssemblyRef.current && phase !== 'collapse' && phase !== 'activation') {
        const pulse = 1.0 + energy.bass * 0.12;
        coreAssemblyRef.current.scale.set(pulse, pulse, pulse);
      }
      // Point light intensity tracks live audio loudness
      if (pointLightRef.current && phase !== 'activation' && phase !== 'collapse') {
        pointLightRef.current.intensity = 4.5 + energy.rms * 8.5;
      }
      // Acrylic internal glow surges with audio energy
      if (acrylicGlowRef.current && phase !== 'activation' && phase !== 'collapse') {
        acrylicGlowRef.current.intensity = 3.0 + energy.rms * 4.0;
      }
      // Copper coil emissive intensity surges with live audio
      if (phase !== 'activation' && phase !== 'collapse') {
        setCopperGlow(0.25 + energy.rms * 0.55);
      }
    }
  });

  // ── Real PBR Materials for Authentic Iron Man Movie Prop ──
  const brushedAluminum = (
    <meshStandardMaterial
      color="#b8c0cc"
      metalness={0.96}
      roughness={0.18}
      envMapIntensity={2.0}
    />
  );

  const darkComposite = (
    <meshStandardMaterial
      color="#12161d"
      metalness={0.85}
      roughness={0.35}
    />
  );

  const mirrorChrome = (
    <meshStandardMaterial
      color="#ffffff"
      metalness={0.98}
      roughness={0.06}
      envMapIntensity={2.5}
    />
  );

  const brassLug = (
    <meshStandardMaterial
      color="#f59e0b"
      metalness={0.92}
      roughness={0.22}
      envMapIntensity={1.8}
    />
  );

  const clearAcrylic = (
    <meshPhysicalMaterial
      color="#001830"
      transmission={0.95}
      roughness={0.04}
      ior={1.52}
      thickness={1.1}
      clearcoat={1.0}
      clearcoatRoughness={0.05}
    />
  );

  return (
    <group>
      {/* Central lighting radiating through the quartz and copper mechanics */}
      <pointLight ref={pointLightRef} color="#00f5ff" intensity={4.5} distance={28} decay={1.4} position={[0, 0, 0.35]} />
      <pointLight ref={coreLightRef} color="#ffffff" intensity={5.5} distance={14} decay={1.8} position={[0, 0, 0.0]} />
      <pointLight ref={acrylicGlowRef} color="#00f5ff" intensity={3.0} distance={18} decay={1.5} position={[0, 0, -0.05]} />

      {/* Beat-synced shockwave ripple ring */}
      <mesh ref={shockwaveRef} position={[0, 0, 0.1]} scale={[0.001, 0.001, 0.001]}>
        <ringGeometry args={[0.9, 1.02, 64]} />
        <meshBasicMaterial color="#00f5ff" transparent opacity={0.75} blending={THREE.AdditiveBlending} side={THREE.DoubleSide} />
      </mesh>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 1: THE CENTRAL QUANTUM ARC CORE (The Heart) (Z: 0.0 to 0.28)
      ───────────────────────────────────────────────────────────── */}
      <group ref={coreAssemblyRef} position={[0, 0, 0.0]}>
        {/* 1. Pure White-Hot Singularity Star (Center) */}
        <mesh position={[0, 0, 0.04]}>
          <sphereGeometry args={[0.36, 32, 32]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>

        {/* 2. Living Vibranium / Palladium Plasma Inner Shell (Electric Cyan) */}
        <mesh position={[0, 0, 0.05]}>
          <sphereGeometry args={[0.54, 32, 32]} />
          <meshBasicMaterial color="#00f5ff" transparent opacity={0.8} blending={THREE.AdditiveBlending} />
        </mesh>

        {/* 3. Stepped Cathode Emitter Rings with micro-teeth */}
        <mesh position={[0, 0, 0.08]}>
          <torusGeometry args={[0.62, 0.045, 16, 48]} />
          <meshBasicMaterial color="#00f5ff" />
        </mesh>
        <mesh position={[0, 0, 0.06]}>
          <torusGeometry args={[0.52, 0.03, 16, 48]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>

        {/* 4. Outer Electric Blue Corona Envelope */}
        <mesh position={[0, 0, 0.05]}>
          <sphereGeometry args={[0.7, 32, 32]} />
          <meshBasicMaterial color="#0044ff" transparent opacity={0.3} blending={THREE.AdditiveBlending} depthWrite={false} />
        </mesh>

        {/* 5. 28 Internal Orbiting Quantum Sparks */}
        <points ref={coreParticlesRef} position={[0, 0, 0.05]}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={particleData.count}
              array={particleData.pos}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            color="#ffffff"
            size={0.075}
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>

        {/* 5b. Multi-Element Anamorphic Lens Flare (Signature Divyanshu Industries Flare) */}
        <mesh position={[0, 0, 0.18]}>
          <planeGeometry args={[5.8, 0.065]} />
          <meshBasicMaterial
            color="#00f5ff"
            transparent
            opacity={phase === 'activation' ? 0.98 : 0.55}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>
        <mesh position={[0, 0, 0.18]}>
          <planeGeometry args={[2.2, 0.14]} />
          <meshBasicMaterial
            color="#ffffff"
            transparent
            opacity={phase === 'activation' ? 0.98 : 0.7}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>
        {/* 4-Point Starburst Flares */}
        <mesh position={[0, 0, 0.18]} rotation={[0, 0, Math.PI / 4]}>
          <planeGeometry args={[0.95, 0.95]} />
          <meshBasicMaterial
            color="#00e5ff"
            transparent
            opacity={phase === 'activation' ? 0.7 : 0.28}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>

        {/* 6. Heavy Convex Borosilicate Quartz Dome Cap */}
        <mesh position={[0, 0, 0.1]} rotation={[Math.PI / 2, 0, 0]}>
          <sphereGeometry args={[0.76, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2.2]} />
          {clearAcrylic}
        </mesh>

        {/* 6b. Concentric Fresnel Caustic Ridges on Lens Surface */}
        {[0.32, 0.52, 0.68].map((radius, idx) => (
          <mesh key={`fresnel-ridge-${idx}`} position={[0, 0, 0.19]}>
            <torusGeometry args={[radius, 0.007, 16, 64]} />
            <meshBasicMaterial
              color="#ffffff"
              transparent
              opacity={0.4}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          </mesh>
        ))}

        {/* 7. Stepped Machined Aluminum Core Heatsink Collar with 6 micro-bolts */}
        <mesh position={[0, 0, 0.12]}>
          <torusGeometry args={[0.82, 0.05, 24, 64]} />
          {brushedAluminum}
        </mesh>
        {Array.from({ length: 6 }).map((_, i) => {
          const a = (i / 6) * Math.PI * 2;
          return (
            <mesh key={`micro-bolt-${i}`} position={[Math.cos(a) * 0.82, Math.sin(a) * 0.82, 0.15]}>
              <cylinderGeometry args={[0.02, 0.02, 0.025, 8]} />
              {mirrorChrome}
            </mesh>
          );
        })}

        {/* 8. Central 3-Point Aperture Teeth (Tri-Aperture spec: 0°, 120°, 240°) */}
        {[0, (2 / 3) * Math.PI, (4 / 3) * Math.PI].map((a, i) => (
          <mesh key={`aperture-tooth-${i}`} position={[Math.cos(a) * 0.65, Math.sin(a) * 0.65, 0.11]} rotation={[0, 0, a]}>
            <boxGeometry args={[0.16, 0.08, 0.04]} />
            {brushedAluminum}
          </mesh>
        ))}
      </group>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 2: CLEAR ACRYLIC BASE RING & INTERNAL DIFFUSER (Z: +0.12)
          In the movie prop, the 10 coils sit on a glowing clear acrylic torus!
      ───────────────────────────────────────────────────────────── */}
      <group ref={acrylicRingRef} position={[0, 0, 0.12]}>
        {/* Full thick laser-cut clear acrylic ring */}
        <mesh>
          <torusGeometry args={[2.16, 0.26, 32, 128]} />
          {clearAcrylic}
        </mesh>

        {/* Internal cyan diffused LED light tube inside the acrylic ring */}
        <mesh position={[0, 0, -0.04]}>
          <torusGeometry args={[2.16, 0.07, 16, 100]} />
          <meshBasicMaterial color="#00f5ff" transparent opacity={0.75} blending={THREE.AdditiveBlending} />
        </mesh>

        {/* Circular PCB printed circuit board ring visible under the acrylic */}
        <mesh position={[0, 0, -0.08]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[2.42, 2.42, 0.02, 64]} />
          <meshStandardMaterial color="#062228" metalness={0.6} roughness={0.4} />
        </mesh>

        {/* 10 SMD Micro-LEDs on the PCB behind each solenoid coil */}
        {Array.from({ length: 10 }).map((_, i) => {
          const angle = (i / 10) * Math.PI * 2 + 0.14;
          const cos = Math.cos(angle);
          const sin = Math.sin(angle);
          const isAmber = i % 3 === 0;
          return (
            <group key={`smd-led-${i}`} position={[cos * 2.38, sin * 2.38, -0.06]}>
              <mesh>
                <boxGeometry args={[0.04, 0.04, 0.02]} />
                <meshStandardMaterial color="#0a1018" metalness={0.9} roughness={0.3} />
              </mesh>
              <mesh position={[0, 0, 0.015]}>
                <boxGeometry args={[0.025, 0.025, 0.01]} />
                <meshBasicMaterial
                  color={isAmber ? '#f59e0b' : '#00f5ff'}
                  transparent
                  opacity={0.9}
                  blending={THREE.AdditiveBlending}
                />
              </mesh>
            </group>
          );
        })}
      </group>

      {/* ── 60 Volumetric Holographic Dust Motes drifting in beam volume ── */}
      <points ref={dustMotesRef} position={[0, 0, 0]}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={dustMotesData.count}
            array={dustMotesData.pos}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#00f5ff"
          size={0.045}
          transparent
          opacity={0.5}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 3: 10 RADIAL CNC ALUMINUM SPOKES & STATOR VENTS (Z: +0.16)
      ───────────────────────────────────────────────────────────── */}
      <group ref={statorSpokesRef} position={[0, 0, 0.16]}>
        {/* Inner collector ring */}
        <mesh>
          <torusGeometry args={[0.94, 0.05, 16, 64]} />
          {brushedAluminum}
        </mesh>

        {/* Laser-cut stator ventilation disc with cooling slots */}
        <mesh position={[0, 0, -0.04]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[1.52, 1.52, 0.03, 48]} />
          {darkComposite}
        </mesh>

        {/* 10 Precision Machined Aluminum Spokes connecting to the 10 Solenoids */}
        {Array.from({ length: 10 }).map((_, i) => {
          const angle = (i / 10) * Math.PI * 2;
          const cos = Math.cos(angle);
          const sin = Math.sin(angle);
          return (
            <group key={`spoke-${i}`}>
              {/* Heavy CNC aluminum truss bar */}
              <mesh rotation={[0, 0, angle]} position={[cos * 1.5, sin * 1.5, 0]}>
                <boxGeometry args={[1.25, 0.12, 0.14]} />
                {brushedAluminum}
              </mesh>
              {/* Inset superconducting cyan bus line running along the spoke */}
              <mesh rotation={[0, 0, angle]} position={[cos * 1.5, sin * 1.5, 0.07]}>
                <boxGeometry args={[1.1, 0.025, 0.03]} />
                <meshBasicMaterial color="#00f5ff" />
              </mesh>
            </group>
          );
        })}
      </group>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 4: THE 10 REAL COPPER-WOUND SOLENOIDS (Divyanshu Industries Spec) (Z: +0.24)
      ───────────────────────────────────────────────────────────── */}
      <group ref={solenoidRingRef} position={[0, 0, 0.24]}>
        {/* 10 Symmetrical Toroidal Solenoid Assemblies */}
        {Array.from({ length: 10 }).map((_, i) => {
          const angle = (i / 10) * Math.PI * 2;
          const cos = Math.cos(angle);
          const sin = Math.sin(angle);
          return (
            <group
              key={`solenoid-${i}`}
              rotation={[0, 0, angle]}
              position={[cos * 2.16, sin * 2.16, 0]}
            >
              {/* 1. Black Phenolic / Composite Core Block */}
              <mesh position={[0, 0, 0]}>
                <boxGeometry args={[0.42, 0.38, 0.38]} />
                {darkComposite}
              </mesh>
              {/* 1b. Holographic Cyan Technical Wireframe Accent */}
              <mesh position={[0, 0, 0]}>
                <boxGeometry args={[0.425, 0.385, 0.385]} />
                <meshBasicMaterial
                  color="#00f5ff"
                  wireframe
                  transparent
                  opacity={0.3}
                  blending={THREE.AdditiveBlending}
                />
              </mesh>

              {/* 2. Superconducting Vibranium Tube Core underneath the wire */}
              <mesh rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.18, 0.18, 0.37, 24]} />
                <meshBasicMaterial color="#00f5ff" transparent opacity={0.75} blending={THREE.AdditiveBlending} />
              </mesh>

              {/* 3. Real 3D Tight Glossy Copper Magnet Wire Windings (8 turns per coil) */}
              {Array.from({ length: 8 }).map((_, j) => (
                <mesh
                  key={`wire-${i}-${j}`}
                  rotation={[Math.PI / 2, 0, 0]}
                  position={[0, (j - 3.5) * 0.042, 0]}
                >
                  <torusGeometry args={[0.23, 0.016, 16, 32]} />
                  <meshStandardMaterial
                    color="#e07a38"
                    emissive="#92400e"
                    emissiveIntensity={copperGlow}
                    metalness={0.98}
                    roughness={0.12}
                    envMapIntensity={2.0}
                  />
                </mesh>
              ))}

              {/* 4. Silver Center Zip-Tie / Retaining Band clamping the copper bundle */}
              <mesh position={[0, 0, 0.2]}>
                <boxGeometry args={[0.26, 0.06, 0.03]} />
                {mirrorChrome}
              </mesh>

              {/* 5. Dual Brass Terminal Solder Lug Tabs */}
              <mesh position={[0.22, 0, 0]}>
                <boxGeometry args={[0.04, 0.16, 0.16]} />
                {brassLug}
              </mesh>
              <mesh position={[-0.22, 0, 0]}>
                <boxGeometry args={[0.04, 0.16, 0.16]} />
                {brassLug}
              </mesh>

              {/* 6. Dual Chrome Terminal Solder Posts */}
              <mesh position={[0.22, 0, 0.08]} rotation={[0, 0, 0]}>
                <cylinderGeometry args={[0.02, 0.02, 0.16, 12]} />
                {mirrorChrome}
              </mesh>
              <mesh position={[-0.22, 0, 0.08]} rotation={[0, 0, 0]}>
                <cylinderGeometry args={[0.02, 0.02, 0.16, 12]} />
                {mirrorChrome}
              </mesh>
            </group>
          );
        })}

        {/* Heavy Curved Silver/Copper Interconnecting Jumper Wire Loop connecting all 10 solenoids */}
        <mesh position={[0, 0, 0.1]}>
          <torusGeometry args={[2.38, 0.018, 16, 100]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.96} roughness={0.15} />
        </mesh>
      </group>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 5: CNC BRUSHED ALUMINUM BEZEL & 20 ALLEN BOLTS (Z: +0.38)
      ───────────────────────────────────────────────────────────── */}
      <group ref={outerBezelRef} position={[0, 0, 0.38]}>
        {/* Main outer retaining aluminum bezel collar */}
        <mesh>
          <torusGeometry args={[2.65, 0.15, 32, 128]} />
          {brushedAluminum}
        </mesh>
        {/* Holographic blueprint wireframe overlay on bezel */}
        <mesh>
          <torusGeometry args={[2.65, 0.155, 16, 64]} />
          <meshBasicMaterial
            color="#00e5ff"
            wireframe
            transparent
            opacity={0.25}
            blending={THREE.AdditiveBlending}
          />
        </mesh>

        {/* Outer chamfered cylindrical cup casing */}
        <mesh position={[0, 0, -0.1]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[2.86, 2.86, 0.1, 64]} />
          {brushedAluminum}
        </mesh>

        {/* 20 Precision Countersunk Allen/Torx Socket-Cap Screws */}
        {Array.from({ length: 20 }).map((_, i) => {
          const angle = (i / 20) * Math.PI * 2;
          const cos = Math.cos(angle);
          const sin = Math.sin(angle);
          return (
            <group key={`bolt-${i}`} position={[cos * 2.68, sin * 2.68, 0.07]}>
              {/* Outer cylindrical bolt head */}
              <mesh rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.045, 0.045, 0.035, 12]} />
                {mirrorChrome}
              </mesh>
              {/* Dark hexagonal socket indentation */}
              <mesh position={[0, 0, 0.018]} rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.022, 0.022, 0.012, 6]} />
                {darkComposite}
              </mesh>
            </group>
          );
        })}

        {/* 3 Heavy External Chest-Mount Retaining Clamps (Divyanshu Industries spec: 0°, 120°, 240°) */}
        {[0, (2 / 3) * Math.PI, (4 / 3) * Math.PI].map((angle, i) => {
          const cos = Math.cos(angle);
          const sin = Math.sin(angle);
          return (
            <group
              key={`chest-mount-${i}`}
              rotation={[0, 0, angle]}
              position={[cos * 2.88, sin * 2.88, 0.02]}
            >
              {/* Rectangular mounting bracket */}
              <mesh>
                <boxGeometry args={[0.22, 0.36, 0.22]} />
                {brushedAluminum}
              </mesh>
              {/* Brass washer plate */}
              <mesh position={[0, 0, 0.11]} rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.07, 0.07, 0.02, 16]} />
                {brassLug}
              </mesh>
              {/* Clamping hex bolt on each lug */}
              <mesh position={[0, 0, 0.13]} rotation={[Math.PI / 2, 0, 0]}>
                <cylinderGeometry args={[0.045, 0.045, 0.04, 12]} />
                {mirrorChrome}
              </mesh>
            </group>
          );
        })}
      </group>
    </group>
  );
}

