import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ScanLaserProps {
  phase: string;
}

export default function ScanLaser({ phase }: ScanLaserProps) {
  const groupRef = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const planeRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    // Active strictly during scanning phase (approx. 18s - 24s in audio)
    if (phase !== 'scanning') return;

    const t = state.clock.elapsedTime;
    // Smooth ping-pong sweep across the face of the Arc Reactor (y: +3.2 to -3.2)
    const y = Math.sin(t * 1.8) * 3.2;

    if (groupRef.current) {
      groupRef.current.position.y = y;
    }
  });

  // Only render during scanning phase
  if (phase !== 'scanning') return null;

  return (
    <group ref={groupRef} position={[0, 0, 0.25]}>
      {/* ── 1. Sharp Glowing Cyan Laser Sweep Plane ── */}
      <mesh ref={planeRef} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[3.2, 64]} />
        <meshBasicMaterial
          color="#00f5ff"
          transparent
          opacity={0.12}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* ── 2. Intense White-Cyan Laser Cut Edge Ring ── */}
      <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[3.15, 3.25, 64]} />
        <meshBasicMaterial
          color="#ffffff"
          transparent
          opacity={0.85}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* ── 3. Horizontal Laser Crosshair Bar ── */}
      <mesh position={[0, 0, 0.02]}>
        <planeGeometry args={[6.4, 0.025]} />
        <meshBasicMaterial
          color="#00ffff"
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>

      {/* ── 4. Floating CAD Dimension Callout Markers ── */}
      {/* Left Callout Tag */}
      <group position={[-3.3, 0, 0.05]}>
        <mesh>
          <planeGeometry args={[0.08, 0.08]} />
          <meshBasicMaterial color="#ffffff" blending={THREE.AdditiveBlending} />
        </mesh>
        <mesh position={[0.2, 0, 0]}>
          <planeGeometry args={[0.3, 0.015]} />
          <meshBasicMaterial color="#00e5ff" blending={THREE.AdditiveBlending} />
        </mesh>
      </group>

      {/* Right Callout Tag */}
      <group position={[3.3, 0, 0.05]}>
        <mesh>
          <planeGeometry args={[0.08, 0.08]} />
          <meshBasicMaterial color="#ffffff" blending={THREE.AdditiveBlending} />
        </mesh>
        <mesh position={[-0.2, 0, 0]}>
          <planeGeometry args={[0.3, 0.015]} />
          <meshBasicMaterial color="#00e5ff" blending={THREE.AdditiveBlending} />
        </mesh>
      </group>
    </group>
  );
}
