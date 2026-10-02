import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface HoloBlueprintRingsProps {
  phase: string;
}

export default function HoloBlueprintRings({ phase }: HoloBlueprintRingsProps) {
  const ring1Ref = useRef<THREE.Group>(null);
  const ring2Ref = useRef<THREE.Group>(null);
  const ring3Ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (ring1Ref.current) ring1Ref.current.rotation.z = t * 0.08;
    if (ring2Ref.current) ring2Ref.current.rotation.z = -t * 0.05;
    if (ring3Ref.current) ring3Ref.current.rotation.z = t * 0.03;
  });

  const isVisible = phase !== 'collapse';

  if (!isVisible) return null;

  return (
    <group position={[0, 0, -0.1]}>
      {/* ── Ring 1: Inner Technical Graduation Ring (R = 1.8) ── */}
      <group ref={ring1Ref}>
        <mesh>
          <ringGeometry args={[1.78, 1.8, 96]} />
          <meshBasicMaterial
            color="#00e5ff"
            transparent
            opacity={0.35}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
          />
        </mesh>
        {/* 36 radial calibration tick marks */}
        {Array.from({ length: 36 }).map((_, i) => {
          const a = (i / 36) * Math.PI * 2;
          const isMajor = i % 3 === 0;
          return (
            <mesh
              key={`tick-${i}`}
              position={[Math.cos(a) * 1.84, Math.sin(a) * 1.84, 0]}
              rotation={[0, 0, a]}
            >
              <planeGeometry args={[isMajor ? 0.09 : 0.04, 0.012]} />
              <meshBasicMaterial
                color="#00e5ff"
                transparent
                opacity={isMajor ? 0.6 : 0.25}
                blending={THREE.AdditiveBlending}
                side={THREE.DoubleSide}
              />
            </mesh>
          );
        })}
      </group>

      {/* ── Ring 2: Middle Concentric Blueprint Ring (R = 3.1) ── */}
      <group ref={ring2Ref}>
        <mesh>
          <ringGeometry args={[3.08, 3.1, 128]} />
          <meshBasicMaterial
            color="#00a8ff"
            transparent
            opacity={0.3}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
          />
        </mesh>
        {/* Segmented dashed arc tracks */}
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2;
          return (
            <mesh
              key={`dash-${i}`}
              position={[Math.cos(a) * 3.16, Math.sin(a) * 3.16, 0]}
              rotation={[0, 0, a]}
            >
              <planeGeometry args={[0.18, 0.015]} />
              <meshBasicMaterial
                color="#00e5ff"
                transparent
                opacity={0.5}
                blending={THREE.AdditiveBlending}
                side={THREE.DoubleSide}
              />
            </mesh>
          );
        })}
      </group>

      {/* ── Ring 3: Outer Horizon Alignment Reticle (R = 3.65) ── */}
      <group ref={ring3Ref}>
        <mesh>
          <ringGeometry args={[3.63, 3.65, 128]} />
          <meshBasicMaterial
            color="#00e5ff"
            transparent
            opacity={0.2}
            blending={THREE.AdditiveBlending}
            side={THREE.DoubleSide}
          />
        </mesh>
        {/* 4 Cardinal Crosshairs */}
        {[0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2].map((a, i) => (
          <mesh
            key={`cardinal-${i}`}
            position={[Math.cos(a) * 3.75, Math.sin(a) * 3.75, 0]}
            rotation={[0, 0, a]}
          >
            <planeGeometry args={[0.3, 0.018]} />
            <meshBasicMaterial
              color="#ffffff"
              transparent
              opacity={0.7}
              blending={THREE.AdditiveBlending}
              side={THREE.DoubleSide}
            />
          </mesh>
        ))}
      </group>
    </group>
  );
}
