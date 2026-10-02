import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface RotatingRingsProps {
  visible?: boolean;
  scale?: number;
  synchronized?: boolean;
}

export default function RotatingRings({ visible = true, scale = 1.0, synchronized = false }: RotatingRingsProps) {
  const ring1Ref = useRef<THREE.Group>(null);
  const ring2Ref = useRef<THREE.Group>(null);
  const ring3Ref = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (synchronized) {
      // In harmonic resonance: all rings lock and rotate at coordinated frequency
      const syncSpeed = 1.2 * delta;
      if (ring1Ref.current) ring1Ref.current.rotation.y += syncSpeed;
      if (ring2Ref.current) ring2Ref.current.rotation.x += syncSpeed;
      if (ring3Ref.current) ring3Ref.current.rotation.z += syncSpeed;
    } else {
      // Independent differential rotation
      if (ring1Ref.current) ring1Ref.current.rotation.y += 0.35 * delta;
      if (ring2Ref.current) ring2Ref.current.rotation.x -= 0.28 * delta;
      if (ring3Ref.current) ring3Ref.current.rotation.z += 0.22 * delta;
    }
  });

  if (!visible) return null;

  return (
    <group scale={scale}>
      {/* ── Ring 1: Inner Containment Ring (Radius 2.6) ── */}
      <group ref={ring1Ref}>
        <mesh>
          <torusGeometry args={[2.6, 0.02, 16, 120]} />
          <meshBasicMaterial 
            color="#00e5ff" 
            transparent 
            opacity={0.8} 
            blending={THREE.AdditiveBlending} 
          />
        </mesh>
        {/* Orbital tick marks */}
        {Array.from({ length: 12 }).map((_, i) => {
          const angle = (i / 12) * Math.PI * 2;
          return (
            <mesh key={i} position={[Math.cos(angle) * 2.6, Math.sin(angle) * 2.6, 0]}>
              <boxGeometry args={[0.04, 0.12, 0.02]} />
              <meshBasicMaterial color="#ffffff" transparent opacity={0.7} />
            </mesh>
          );
        })}
      </group>

      {/* ── Ring 2: Counter-Rotating Mechanical Ring (Radius 3.2, Tilted) ── */}
      <group ref={ring2Ref} rotation={[0, 0, THREE.MathUtils.degToRad(35)]}>
        <mesh>
          <torusGeometry args={[3.2, 0.018, 16, 120]} />
          <meshBasicMaterial 
            color="#00a8ff" 
            transparent 
            opacity={0.75} 
            blending={THREE.AdditiveBlending} 
          />
        </mesh>
        {/* Notched marker segments */}
        {Array.from({ length: 8 }).map((_, i) => {
          const angle = (i / 8) * Math.PI * 2;
          return (
            <mesh key={i} position={[Math.cos(angle) * 3.2, 0, Math.sin(angle) * 3.2]}>
              <sphereGeometry args={[0.05, 8, 8]} />
              <meshBasicMaterial color="#00e5ff" blending={THREE.AdditiveBlending} />
            </mesh>
          );
        })}
      </group>

      {/* ── Ring 3: Outer Orbital Data Ring (Radius 3.8, Tilted) ── */}
      <group ref={ring3Ref} rotation={[THREE.MathUtils.degToRad(-25), 0, 0]}>
        <mesh>
          <torusGeometry args={[3.8, 0.015, 16, 120]} />
          <meshBasicMaterial 
            color="#00ffff" 
            transparent 
            opacity={0.6} 
            blending={THREE.AdditiveBlending} 
          />
        </mesh>
      </group>
    </group>
  );
}
