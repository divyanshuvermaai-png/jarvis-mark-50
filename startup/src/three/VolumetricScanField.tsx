import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface VolumetricScanFieldProps {
  visible?: boolean;
  speed?: number;
  onScanProgress?: (y: number) => void;
}

export default function VolumetricScanField({ visible = true, speed = 1.0, onScanProgress }: VolumetricScanFieldProps) {
  const groupRef = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const cylinderRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!visible) return;
    const t = state.clock.elapsedTime * speed;
    // Ping-pong volumetric sweep between Y = -3.8 and Y = 3.8
    const y = Math.sin(t * 1.5) * 3.8;

    if (groupRef.current) {
      groupRef.current.position.y = y;
    }

    if (ringRef.current) {
      ringRef.current.rotation.z += 0.05;
    }

    if (onScanProgress) {
      onScanProgress(y);
    }
  });

  if (!visible) return null;

  return (
    <group ref={groupRef}>
      {/* ── 1. Volumetric Cylindrical Light Sheath (Vertical Depth) ── */}
      <mesh ref={cylinderRef}>
        <cylinderGeometry args={[4.2, 4.2, 0.9, 36, 1, true]} />
        <meshBasicMaterial
          color="#00e5ff"
          transparent
          opacity={0.18}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* ── 2. Primary High-Intensity Laser Intersection Ring ── */}
      <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[4.1, 4.25, 48]} />
        <meshBasicMaterial
          color="#ffffff"
          transparent
          opacity={0.95}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* ── 3. Internal Secondary Scan Aperture Ring ── */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.1, 2.18, 36]} />
        <meshBasicMaterial
          color="#00e5ff"
          transparent
          opacity={0.85}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* ── 4. Spatial Intersection Laser Crosshair Guides ── */}
      {[0, Math.PI / 2].map((angle, i) => (
        <mesh key={i} rotation={[0, angle, 0]}>
          <boxGeometry args={[8.4, 0.02, 0.02]} />
          <meshBasicMaterial color="#00e5ff" transparent opacity={0.4} blending={THREE.AdditiveBlending} />
        </mesh>
      ))}
    </group>
  );
}
