import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface VolumetricParticlesProps {
  visible?: boolean;
  synchronized?: boolean;
  activationTrigger?: boolean;
}

export default function VolumetricParticles({
  visible = true,
  synchronized = false,
  activationTrigger = false,
}: VolumetricParticlesProps) {
  const fgPointsRef = useRef<THREE.Points>(null);
  const midPointsRef = useRef<THREE.Points>(null);
  const bgPointsRef = useRef<THREE.Points>(null);

  // 1. Foreground Motes (Close to camera, Z: 5 to 10)
  const [fgPositions, fgVelocities] = useMemo(() => {
    const count = 100;
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 12;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = 5 + Math.random() * 5; // Close to camera

      vel[i * 3] = (Math.random() - 0.5) * 0.15;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.15;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.1;
    }

    return [pos, vel];
  }, []);

  // 2. Midground Machine Stream (Orbiting the reactor, R: 2.0 to 4.0)
  const [midPositions, midAngles, midRadii] = useMemo(() => {
    const count = 800;
    const pos = new Float32Array(count * 3);
    const angles = new Float32Array(count);
    const radii = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const r = 2.0 + Math.random() * 2.2;
      const angle = Math.random() * Math.PI * 2;
      const y = (Math.random() - 0.5) * 3.4;

      pos[i * 3] = Math.cos(angle) * r;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = Math.sin(angle) * r;

      angles[i] = angle;
      radii[i] = r;
    }

    return [pos, angles, radii];
  }, []);

  // 3. Deep Background Field (R: 10 to 18)
  const bgPositions = useMemo(() => {
    const count = 1000;
    const pos = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const r = 10 + Math.random() * 8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }

    return pos;
  }, []);

  useFrame((state, delta) => {
    // ── Animate Foreground Motes ──
    if (fgPointsRef.current) {
      const pos = fgPointsRef.current.geometry.attributes.position.array as Float32Array;
      const count = pos.length / 3;

      for (let i = 0; i < count; i++) {
        pos[i * 3] += fgVelocities[i * 3] * delta;
        pos[i * 3 + 1] += fgVelocities[i * 3 + 1] * delta;
        pos[i * 3 + 2] += fgVelocities[i * 3 + 2] * delta;

        // Wrap bounds
        if (pos[i * 3] > 7) pos[i * 3] = -7;
        if (pos[i * 3] < -7) pos[i * 3] = 7;
        if (pos[i * 3 + 1] > 5) pos[i * 3 + 1] = -5;
        if (pos[i * 3 + 1] < -5) pos[i * 3 + 1] = 5;
        if (pos[i * 3 + 2] > 11) pos[i * 3 + 2] = 5;
        if (pos[i * 3 + 2] < 5) pos[i * 3 + 2] = 11;
      }
      fgPointsRef.current.geometry.attributes.position.needsUpdate = true;
    }

    // ── Animate Midground Machine Stream ──
    if (midPointsRef.current) {
      const pos = midPointsRef.current.geometry.attributes.position.array as Float32Array;
      const count = pos.length / 3;
      const speed = synchronized ? 1.4 : 0.6;

      for (let i = 0; i < count; i++) {
        midAngles[i] += (speed / (midRadii[i] + 0.5)) * delta;
        const angle = midAngles[i];
        let r = midRadii[i];

        if (activationTrigger) {
          // Particles violently repelled outward on activation pulse
          r += 4.0 * delta;
        }

        pos[i * 3] = Math.cos(angle) * r;
        pos[i * 3 + 2] = Math.sin(angle) * r;
      }
      midPointsRef.current.geometry.attributes.position.needsUpdate = true;
    }

    // ── Deep Background Slow Yaw Drift ──
    if (bgPointsRef.current) {
      bgPointsRef.current.rotation.y += 0.012 * delta;
    }
  });

  if (!visible) return null;

  return (
    <group>
      {/* ── Tier 1: Foreground Luminous Bokeh Motes ── */}
      <points ref={fgPointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={fgPositions.length / 3}
            array={fgPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.14}
          color="#cceeff"
          transparent
          opacity={0.45}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* ── Tier 2: Midground Machine Stream (Conduit Orbiters) ── */}
      <points ref={midPointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={midPositions.length / 3}
            array={midPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.045}
          color="#00e5ff"
          transparent
          opacity={0.8}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* ── Tier 3: Deep Background Ambient Nebula Field ── */}
      <points ref={bgPointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={bgPositions.length / 3}
            array={bgPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.025}
          color="#0055ff"
          transparent
          opacity={0.35}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}
