import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';

interface MechanicalIrisProps {
  phase: 'folded' | 'assembling' | 'open' | 'collapsing';
  onComplete?: () => void;
  onLatchSound?: () => void;
}

export default function MechanicalIris({ phase, onComplete, onLatchSound }: MechanicalIrisProps) {
  const groupRef = useRef<THREE.Group>(null);
  const bladeRefs = useRef<(THREE.Group | null)[]>([]);

  useEffect(() => {
    bladeRefs.current.forEach((blade, i) => {
      if (!blade) return;
      const angle = (i / 6) * Math.PI * 2;
      const mesh = blade.children[0] as THREE.Mesh;

      if (phase === 'folded') {
        gsap.set(blade.position, { x: 0, y: 0, z: 0 });
        gsap.set(mesh.rotation, { z: 0 });
      } else if (phase === 'assembling') {
        // Physical spring-like unfolding
        gsap.to(blade.position, {
          x: Math.cos(angle) * 2.3,
          y: Math.sin(angle) * 2.3,
          duration: 3.2,
          delay: i * 0.08,
          ease: "power3.out",
          onComplete: () => {
            if (i === 5 && onLatchSound) onLatchSound();
          }
        });
        gsap.to(mesh.rotation, {
          z: Math.PI / 4.5,
          duration: 3.2,
          delay: i * 0.08,
          ease: "power3.out"
        });
      } else if (phase === 'open') {
        gsap.to(blade.position, {
          x: Math.cos(angle) * 2.3,
          y: Math.sin(angle) * 2.3,
          duration: 1.0,
          ease: "power2.out"
        });
      } else if (phase === 'collapsing') {
        // Retract inward to singularity
        gsap.to(blade.position, {
          x: 0,
          y: 0,
          duration: 2.2,
          ease: "power3.in",
          onComplete: i === 0 ? onComplete : undefined
        });
        gsap.to(mesh.rotation, {
          z: 0,
          duration: 2.2,
          ease: "power3.in"
        });
      }
    });
  }, [phase, onComplete, onLatchSound]);

  // Subtle breathing rotation while open
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.z += 0.015 * delta;
    }
  });

  return (
    <group ref={groupRef}>
      {Array.from({ length: 6 }).map((_, i) => {
        const angle = (i / 6) * Math.PI * 2;
        return (
          <group 
            key={i} 
            rotation={[0, 0, angle]}
            ref={(el) => { bladeRefs.current[i] = el; }}
          >
            {/* Main Iris Segment */}
            <mesh position={[1.45, 0, 0]}>
              <boxGeometry args={[1.55, 0.38, 0.08]} />
              <meshStandardMaterial 
                color="#001428" 
                emissive="#00e5ff" 
                emissiveIntensity={0.65} 
                metalness={0.9} 
                roughness={0.15} 
              />
            </mesh>

            {/* Glowing Energy Conduit Along Blade Edge */}
            <mesh position={[1.45, 0.16, 0.05]}>
              <boxGeometry args={[1.4, 0.04, 0.04]} />
              <meshBasicMaterial 
                color="#00e5ff" 
                transparent 
                opacity={0.9} 
                blending={THREE.AdditiveBlending} 
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}
