import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { ReactorSubPhase } from './ReactorScene';

export default function ArcEnvironment({ phase }: { phase: ReactorSubPhase }) {
  const particlesRef = useRef<THREE.Points>(null);
  const hazeRef = useRef<THREE.Mesh>(null);

  const particleCount = 45; // Minimal, intentional
  const [positions, scales] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const sc = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i++) {
      const r = 4 + Math.random() * 5;
      const theta = Math.random() * Math.PI * 2;
      const y = (Math.random() - 0.5) * 5;
      pos[i * 3] = Math.cos(theta) * r;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = Math.sin(theta) * r;
      sc[i] = Math.random() * 0.04 + 0.02;
    }
    return [pos, sc];
  }, []);

  useEffect(() => {
    if (phase === 'collapse') {
      if (particlesRef.current) {
        gsap.to(particlesRef.current.scale, { x: 0.001, y: 0.001, z: 0.001, duration: 2.0, ease: 'power3.inOut' });
      }
      if (hazeRef.current) {
        gsap.to(hazeRef.current.scale, { x: 0.001, y: 0.001, z: 0.001, duration: 2.5, ease: 'power3.inOut' });
      }
    }
  }, [phase]);

  useFrame((state) => {
    if (!particlesRef.current) return;
    const t = state.clock.elapsedTime;
    particlesRef.current.rotation.y = t * 0.015; // Extremely slow drift
    particlesRef.current.position.y = Math.sin(t * 0.3) * 0.3; // Subtle bobbing
  });

  return (
    <group>
      {/* Subtle blue atmospheric haze */}
      <mesh ref={hazeRef}>
        <sphereGeometry args={[10, 32, 32]} />
        <meshBasicMaterial
          color="#002244"
          transparent
          opacity={0.04}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Minimal Holographic Dust */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={particleCount} array={positions} itemSize={3} />
          <bufferAttribute attach="attributes-size" count={particleCount} array={scales} itemSize={1} />
        </bufferGeometry>
        <pointsMaterial
          color="#00e5ff"
          transparent
          opacity={0.5}
          size={0.15}
          sizeAttenuation={true}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}
