import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { AudioSync } from '../audio/AudioSync';

interface EmberTrailsProps {
  phase: string;
  audioSync?: AudioSync | null;
}

export default function EmberTrails({ phase, audioSync }: EmberTrailsProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const trailsRef = useRef<THREE.Group>(null);

  const count = 120;

  const data = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const orbits = new Float32Array(count * 4); // radius, speed, phase, elevation

    for (let i = 0; i < count; i++) {
      const radius = 0.4 + Math.random() * 2.4;
      const speed = (0.3 + Math.random() * 1.2) * (Math.random() > 0.5 ? 1 : -1);
      const theta = Math.random() * Math.PI * 2;
      const elev = (Math.random() - 0.5) * 1.2;

      orbits[i * 4] = radius;
      orbits[i * 4 + 1] = speed;
      orbits[i * 4 + 2] = theta;
      orbits[i * 4 + 3] = elev;

      positions[i * 3] = Math.cos(theta) * radius;
      positions[i * 3 + 1] = elev;
      positions[i * 3 + 2] = Math.sin(theta) * radius * 0.3;

      // Color: white-hot core sparks → cyan outer sparks
      const t = radius / 2.8;
      colors[i * 3] = 1.0 - t * 0.6;     // R
      colors[i * 3 + 1] = 1.0 - t * 0.1; // G
      colors[i * 3 + 2] = 1.0;            // B

      sizes[i] = 0.02 + Math.random() * 0.06;
    }

    return { positions, colors, sizes, orbits };
  }, []);

  // Burst sparks state
  const burstRef = useRef<{ active: boolean; time: number; particles: Float32Array; velocities: Float32Array }>({
    active: false,
    time: 0,
    particles: new Float32Array(40 * 3),
    velocities: new Float32Array(40 * 3),
  });
  const burstPointsRef = useRef<THREE.Points>(null);

  const burstData = useMemo(() => {
    const pos = new Float32Array(40 * 3);
    const col = new Float32Array(40 * 3);
    for (let i = 0; i < 40; i++) {
      col[i * 3] = 1.0;
      col[i * 3 + 1] = 0.95;
      col[i * 3 + 2] = 0.85;
    }
    return { pos, col };
  }, []);

  // Track phase changes to trigger bursts
  const prevPhaseRef = useRef(phase);

  useFrame((state, delta) => {
    if (phase === 'collapse') return;
    const t = state.clock.elapsedTime;

    // Audio energy
    let audioBoost = 0;
    if (audioSync) {
      const energy = audioSync.getEnergy();
      audioBoost = energy.rms;
    }

    // Trigger burst on phase transitions
    if (prevPhaseRef.current !== phase) {
      if (phase === 'scanning' || phase === 'activation') {
        const burst = burstRef.current;
        burst.active = true;
        burst.time = 0;
        for (let i = 0; i < 40; i++) {
          const angle = Math.random() * Math.PI * 2;
          const speed = 2.5 + Math.random() * 4.0;
          burst.particles[i * 3] = 0;
          burst.particles[i * 3 + 1] = 0;
          burst.particles[i * 3 + 2] = 0;
          burst.velocities[i * 3] = Math.cos(angle) * speed;
          burst.velocities[i * 3 + 1] = (Math.random() - 0.3) * speed * 0.5;
          burst.velocities[i * 3 + 2] = Math.sin(angle) * speed * 0.3;
        }
      }
      prevPhaseRef.current = phase;
    }

    // Update orbital embers
    if (pointsRef.current) {
      const posAttr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;
      const sizeAttr = pointsRef.current.geometry.attributes.size as THREE.BufferAttribute;
      const sArr = sizeAttr.array as Float32Array;

      for (let i = 0; i < count; i++) {
        const radius = data.orbits[i * 4];
        const speed = data.orbits[i * 4 + 1];
        let theta = data.orbits[i * 4 + 2];
        const elev = data.orbits[i * 4 + 3];

        theta += speed * delta * (0.8 + audioBoost * 0.8);
        data.orbits[i * 4 + 2] = theta;

        arr[i * 3] = Math.cos(theta) * radius;
        arr[i * 3 + 1] = elev + Math.sin(t * 2.0 + i) * 0.15;
        arr[i * 3 + 2] = Math.sin(theta) * radius * 0.3;

        // Flicker size with audio
        sArr[i] = data.sizes[i] * (0.7 + audioBoost * 0.8 + Math.sin(t * 15 + i * 3) * 0.15);
      }
      posAttr.needsUpdate = true;
      sizeAttr.needsUpdate = true;
    }

    // Update burst sparks
    const burst = burstRef.current;
    if (burst.active && burstPointsRef.current) {
      burst.time += delta;
      const posAttr = burstPointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;

      for (let i = 0; i < 40; i++) {
        burst.particles[i * 3] += burst.velocities[i * 3] * delta;
        burst.particles[i * 3 + 1] += burst.velocities[i * 3 + 1] * delta;
        burst.particles[i * 3 + 2] += burst.velocities[i * 3 + 2] * delta;

        // Drag
        burst.velocities[i * 3] *= 0.96;
        burst.velocities[i * 3 + 1] *= 0.96;
        burst.velocities[i * 3 + 2] *= 0.96;

        arr[i * 3] = burst.particles[i * 3];
        arr[i * 3 + 1] = burst.particles[i * 3 + 1];
        arr[i * 3 + 2] = burst.particles[i * 3 + 2];
      }
      posAttr.needsUpdate = true;

      // Fade out burst material
      const mat = burstPointsRef.current.material as THREE.PointsMaterial;
      mat.opacity = Math.max(0, 1.0 - burst.time / 0.8);

      if (burst.time > 0.8) {
        burst.active = false;
      }
    }
  });

  if (phase === 'collapse') return null;

  return (
    <group>
      {/* Orbital Ember Sparks */}
      <points ref={pointsRef} position={[0, 0, 0.1]}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={count} array={data.positions} itemSize={3} />
          <bufferAttribute attach="attributes-color" count={count} array={data.colors} itemSize={3} />
          <bufferAttribute attach="attributes-size" count={count} array={data.sizes} itemSize={1} />
        </bufferGeometry>
        <pointsMaterial
          vertexColors
          size={0.06}
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          sizeAttenuation
        />
      </points>

      {/* Burst Sparks (on beat impacts) */}
      <points ref={burstPointsRef} position={[0, 0, 0.1]}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={40} array={burstData.pos} itemSize={3} />
          <bufferAttribute attach="attributes-color" count={40} array={burstData.col} itemSize={3} />
        </bufferGeometry>
        <pointsMaterial
          vertexColors
          size={0.09}
          transparent
          opacity={1.0}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          sizeAttenuation
        />
      </points>
    </group>
  );
}
