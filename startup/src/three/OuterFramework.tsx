import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface OuterFrameworkProps {
  visible?: boolean;
  assemblyProgress?: number; // 0 to 1
}

export default function OuterFramework({ visible = true, assemblyProgress = 1.0 }: OuterFrameworkProps) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.z += 0.025 * delta;
    }
  });

  const hexLine = useMemo(() => {
    const hexRadius = 4.8;
    const numVertices = 6;
    const points: THREE.Vector3[] = [];
    
    for (let i = 0; i <= numVertices; i++) {
      const angle = (i / numVertices) * Math.PI * 2;
      points.push(new THREE.Vector3(Math.cos(angle) * hexRadius, Math.sin(angle) * hexRadius, 0));
    }

    const geom = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#00a8ff'),
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
    });
    return new THREE.Line(geom, mat);
  }, []);

  if (!visible || assemblyProgress <= 0.05) return null;

  const hexRadius = 4.8 * Math.min(assemblyProgress * 1.2, 1.0);

  return (
    <group ref={groupRef} scale={[assemblyProgress, assemblyProgress, assemblyProgress]}>
      {/* Outer Hexagonal Structure */}
      <primitive object={hexLine} />

      {/* Hexagonal Corner Sensor Nodes */}
      {Array.from({ length: 6 }).map((_, i) => {
        const angle = (i / 6) * Math.PI * 2;
        const x = Math.cos(angle) * hexRadius;
        const y = Math.sin(angle) * hexRadius;
        return (
          <group key={i} position={[x, y, 0]}>
            <mesh>
              <sphereGeometry args={[0.08, 16, 16]} />
              <meshBasicMaterial 
                color="#00e5ff" 
                transparent 
                opacity={0.85 * assemblyProgress} 
                blending={THREE.AdditiveBlending} 
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}
