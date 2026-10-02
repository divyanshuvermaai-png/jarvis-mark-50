import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ActivationShockwaveProps {
  trigger: boolean;
}

export default function ActivationShockwave({ trigger }: ActivationShockwaveProps) {
  const shockwaveRef = useRef<THREE.Mesh>(null);
  const startTimeRef = useRef<number | null>(null);

  useFrame((state) => {
    if (!trigger) {
      startTimeRef.current = null;
      if (shockwaveRef.current) {
        shockwaveRef.current.scale.set(0, 0, 0);
      }
      return;
    }

    if (startTimeRef.current === null) {
      startTimeRef.current = state.clock.elapsedTime;
    }

    const elapsed = state.clock.elapsedTime - startTimeRef.current;
    const duration = 2.0;

    if (shockwaveRef.current) {
      if (elapsed < duration) {
        const progress = elapsed / duration;
        // Exponential expansion curve
        const scale = Math.pow(progress, 0.6) * 14.0;
        shockwaveRef.current.scale.set(scale, scale, scale);

        const mat = shockwaveRef.current.material as THREE.MeshBasicMaterial;
        mat.opacity = Math.max(0, (1.0 - progress) * 0.85);
      } else {
        shockwaveRef.current.scale.set(0, 0, 0);
      }
    }
  });

  return (
    <mesh ref={shockwaveRef} rotation={[-Math.PI / 2, 0, 0]} scale={[0, 0, 0]}>
      <ringGeometry args={[0.95, 1.05, 64]} />
      <meshBasicMaterial 
        color="#00e5ff" 
        transparent 
        opacity={0.85} 
        side={THREE.DoubleSide}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}
