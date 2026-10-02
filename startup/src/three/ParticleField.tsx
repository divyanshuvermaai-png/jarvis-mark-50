import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ParticleFieldProps {
  visible?: boolean;
  count?: number;
}

export default function ParticleField({ visible = true, count = 2000 }: ParticleFieldProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const largePointsRef = useRef<THREE.Points>(null);

  const [positions, largePositions] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 1 + Math.random() * 7;
      const theta = 2 * Math.PI * Math.random();
      const phi = Math.acos(2 * Math.random() - 1);
      
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    
    const largePos = new Float32Array(50 * 3);
    for (let i = 0; i < 50; i++) {
      const r = 2 + Math.random() * 4;
      const theta = 2 * Math.PI * Math.random();
      const phi = Math.acos(2 * Math.random() - 1);
      
      largePos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      largePos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      largePos[i * 3 + 2] = r * Math.cos(phi);
    }

    return [pos, largePos];
  }, [count]);

  useFrame((state, delta) => {
    if (pointsRef.current) {
      const positions = pointsRef.current.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < count; i++) {
        const x = positions[i * 3];
        const y = positions[i * 3 + 1];
        const z = positions[i * 3 + 2];
        
        const length = Math.sqrt(x*x + y*y + z*z);
        const speed = 0.5 * delta;
        
        if (length > 8) {
          const r = 1.0;
          positions[i * 3] = (x / length) * r;
          positions[i * 3 + 1] = (y / length) * r;
          positions[i * 3 + 2] = (z / length) * r;
        } else {
          positions[i * 3] += (x / length) * speed;
          positions[i * 3 + 1] += (y / length) * speed;
          positions[i * 3 + 2] += (z / length) * speed;
        }
      }
      pointsRef.current.geometry.attributes.position.needsUpdate = true;
      pointsRef.current.rotation.y += 0.05 * delta;
    }
    
    if (largePointsRef.current) {
      largePointsRef.current.rotation.y -= 0.03 * delta;
      const time = state.clock.elapsedTime;
      const scale = 1.0 + Math.sin(time * 5.0) * 0.5;
      const mat = largePointsRef.current.material as THREE.PointsMaterial;
      mat.size = 0.08 * scale;
    }
  });

  if (!visible) return null;

  return (
    <group>
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={count}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.03}
          color="#00e5ff"
          transparent
          opacity={0.6}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
      <points ref={largePointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={50}
            array={largePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.08}
          color="#ffffff"
          transparent
          opacity={0.9}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}
