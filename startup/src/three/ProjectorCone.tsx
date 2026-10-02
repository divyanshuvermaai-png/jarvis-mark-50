import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ProjectorConeProps {
  phase: string;
}

export default function ProjectorCone({ phase }: ProjectorConeProps) {
  const coneRef = useRef<THREE.Mesh>(null);
  const beamLinesRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (coneRef.current) {
      // Subtle pulse in projection cone opacity
      const mat = coneRef.current.material as THREE.MeshBasicMaterial;
      if (mat) {
        mat.opacity = 0.08 + Math.sin(t * 3.0) * 0.025;
      }
    }
    if (beamLinesRef.current) {
      beamLinesRef.current.rotation.y = t * 0.05;
    }
  });

  const isVisible = phase !== 'collapse';

  if (!isVisible) return null;

  return (
    <group position={[0, -2.2, -0.4]}>
      {/* ── Soft Volumetric Inverted Projection Cone ── */}
      <mesh ref={coneRef} rotation={[0, 0, 0]}>
        <cylinderGeometry args={[2.8, 0.4, 4.4, 32, 1, true]} />
        <meshBasicMaterial
          color="#00e5ff"
          transparent
          opacity={0.09}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>

      {/* ── Vertical Holographic Laser Guide Beams ── */}
      <group ref={beamLinesRef}>
        {Array.from({ length: 8 }).map((_, i) => {
          const a = (i / 8) * Math.PI * 2;
          return (
            <mesh
              key={`beam-${i}`}
              position={[Math.cos(a) * 1.6, 0, Math.sin(a) * 1.6]}
            >
              <cylinderGeometry args={[0.008, 0.008, 4.4, 8]} />
              <meshBasicMaterial
                color="#00ffff"
                transparent
                opacity={0.25}
                blending={THREE.AdditiveBlending}
                depthWrite={false}
              />
            </mesh>
          );
        })}
      </group>

      {/* ── Projection Base Aperture Ring (at the bottom) ── */}
      <mesh position={[0, -2.2, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.3, 0.45, 32]} />
        <meshBasicMaterial
          color="#00e5ff"
          transparent
          opacity={0.5}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}
