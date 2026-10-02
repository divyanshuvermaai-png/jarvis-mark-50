import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';

interface ArticulatedChassisProps {
  phase: 'folded' | 'assembling' | 'open' | 'collapsing';
  onComplete?: () => void;
  onLatchSound?: () => void;
}

export default function ArticulatedChassis({ phase, onComplete, onLatchSound }: ArticulatedChassisProps) {
  const rootGroupRef = useRef<THREE.Group>(null);
  const upperArchRef = useRef<THREE.Group>(null);
  const lowerArchRef = useRef<THREE.Group>(null);
  const solenoidRefs = useRef<(THREE.Group | null)[]>([]);
  const gantryArmRef = useRef<THREE.Group>(null);

  useEffect(() => {
    if (phase === 'folded') {
      if (upperArchRef.current) gsap.set(upperArchRef.current.position, { y: 0.4, z: 0 });
      if (lowerArchRef.current) gsap.set(lowerArchRef.current.position, { y: -0.4, z: 0 });
      if (gantryArmRef.current) gsap.set(gantryArmRef.current.position, { x: 2.0 });
      solenoidRefs.current.forEach(sol => {
        if (sol) gsap.set(sol.position, { z: 0 });
      });
    } else if (phase === 'assembling') {
      // 1. Upper & Lower Armored Gantry Arches articulate outward on pneumatic travel
      if (upperArchRef.current) {
        gsap.to(upperArchRef.current.position, {
          y: 2.1,
          duration: 3.6,
          ease: "power3.out",
          onComplete: () => {
            if (onLatchSound) onLatchSound();
          }
        });
      }
      if (lowerArchRef.current) {
        gsap.to(lowerArchRef.current.position, {
          y: -2.1,
          duration: 3.6,
          ease: "power3.out"
        });
      }

      // 2. Heavy Magnetic Solenoids extend radially and lock
      solenoidRefs.current.forEach((sol, i) => {
        if (!sol) return;
        const angle = (i / 4) * Math.PI * 2;
        gsap.fromTo(sol.position,
          { x: Math.cos(angle) * 1.8, z: Math.sin(angle) * 1.8 },
          {
            x: Math.cos(angle) * 3.4,
            z: Math.sin(angle) * 3.4,
            duration: 3.4,
            delay: i * 0.12,
            ease: "power3.out"
          }
        );
      });

      // 3. Asymmetrical Diagnostic Gantry unfolds
      if (gantryArmRef.current) {
        gsap.to(gantryArmRef.current.position, {
          x: 4.1,
          duration: 4.0,
          ease: "power3.out"
        });
      }
    } else if (phase === 'collapsing') {
      // Retract and collapse inward to the center
      if (upperArchRef.current) {
        gsap.to(upperArchRef.current.position, {
          y: 0,
          duration: 2.6,
          ease: "power3.in",
          onComplete
        });
      }
      if (lowerArchRef.current) {
        gsap.to(lowerArchRef.current.position, {
          y: 0,
          duration: 2.6,
          ease: "power3.in"
        });
      }
      solenoidRefs.current.forEach((sol, i) => {
        if (sol) {
          gsap.to(sol.position, {
            x: 0,
            z: 0,
            duration: 2.4,
            delay: i * 0.05,
            ease: "power3.in"
          });
        }
      });
      if (gantryArmRef.current) {
        gsap.to(gantryArmRef.current.position, {
          x: 0,
          duration: 2.4,
          ease: "power3.in"
        });
      }
    }
  }, [phase, onComplete, onLatchSound]);

  useFrame((state, delta) => {
    // Majestic, steady overall yaw rotation
    if (rootGroupRef.current) {
      rootGroupRef.current.rotation.y += 0.08 * delta;
    }
  });

  const heavyArmorMaterial = (
    <meshStandardMaterial
      color="#011428"
      emissive="#0077b6"
      emissiveIntensity={0.5}
      metalness={0.92}
      roughness={0.18}
      transparent
      opacity={0.88}
    />
  );

  const glowingCyanConduit = (
    <meshBasicMaterial
      color="#00e5ff"
      transparent
      opacity={0.88}
      blending={THREE.AdditiveBlending}
    />
  );

  return (
    <group ref={rootGroupRef}>
      {/* ── 1. Upper Armored Gantry Arch (Segmented Curved 3D Shell) ── */}
      <group ref={upperArchRef} position={[0, 2.1, 0]}>
        {/* Curved Segment 1: Quadrant Arch */}
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[3.2, 3.2, 0.45, 32, 1, true, -Math.PI / 3, (Math.PI * 2) / 3]} />
          {heavyArmorMaterial}
        </mesh>
        {/* Opposing Arch Segment */}
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[3.2, 3.2, 0.45, 32, 1, true, (Math.PI * 2) / 3, (Math.PI * 2) / 3]} />
          {heavyArmorMaterial}
        </mesh>
        {/* Glowing Structural Rib Edges */}
        <mesh position={[0, 0.24, 0]}>
          <torusGeometry args={[3.2, 0.03, 16, 64]} />
          {glowingCyanConduit}
        </mesh>
        {/* Pneumatic Vertical Guide Struts */}
        {[-1.2, 1.2].map((x, i) => (
          <mesh key={i} position={[x, -0.6, 0]}>
            <cylinderGeometry args={[0.06, 0.06, 1.2, 16]} />
            {heavyArmorMaterial}
          </mesh>
        ))}
      </group>

      {/* ── 2. Lower Armored Gantry Arch (Inverted Symmetrical Shell) ── */}
      <group ref={lowerArchRef} position={[0, -2.1, 0]}>
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[3.2, 3.2, 0.45, 32, 1, true, -Math.PI / 3, (Math.PI * 2) / 3]} />
          {heavyArmorMaterial}
        </mesh>
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[3.2, 3.2, 0.45, 32, 1, true, (Math.PI * 2) / 3, (Math.PI * 2) / 3]} />
          {heavyArmorMaterial}
        </mesh>
        <mesh position={[0, -0.24, 0]}>
          <torusGeometry args={[3.2, 0.03, 16, 64]} />
          {glowingCyanConduit}
        </mesh>
        {[-1.2, 1.2].map((x, i) => (
          <mesh key={i} position={[x, 0.6, 0]}>
            <cylinderGeometry args={[0.06, 0.06, 1.2, 16]} />
            {heavyArmorMaterial}
          </mesh>
        ))}
      </group>

      {/* ── 3. Four Heavy Magnetic Containment Solenoids (At 90° Quadrants) ── */}
      {[0, Math.PI / 2, Math.PI, Math.PI * 1.5].map((angle, i) => {
        return (
          <group 
            key={i} 
            ref={(el) => { solenoidRefs.current[i] = el; }}
            position={[Math.cos(angle) * 3.4, 0, Math.sin(angle) * 3.4]}
            rotation={[0, -angle, 0]}
          >
            {/* Cylindrical Magnetic Housing */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.42, 0.42, 0.85, 20]} />
              {heavyArmorMaterial}
            </mesh>
            {/* Glowing Internal Copper-Cyan Coil Core */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.26, 0.26, 0.88, 16]} />
              <meshBasicMaterial 
                color="#00ffff" 
                transparent 
                opacity={0.92} 
                blending={THREE.AdditiveBlending} 
              />
            </mesh>
            {/* Articulated Support Bracket */}
            <mesh position={[-0.45, 0, 0]}>
              <boxGeometry args={[0.5, 0.15, 0.25]} />
              {heavyArmorMaterial}
            </mesh>
          </group>
        );
      })}

      {/* ── 4. Asymmetrical Diagnostic Gantry Arm with Optical Pod ── */}
      <group ref={gantryArmRef} position={[4.1, 0.2, 0]}>
        {/* Cantilever Gantry Truss */}
        <mesh position={[-0.6, 0, 0]}>
          <boxGeometry args={[1.2, 0.12, 0.16]} />
          {heavyArmorMaterial}
        </mesh>
        {/* Sensor Module Housing */}
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[0.38, 0.55, 0.38]} />
          {heavyArmorMaterial}
        </mesh>
        {/* Optical Sensor Aperture */}
        <mesh position={[-0.2, 0, 0]} rotation={[0, -Math.PI / 2, 0]}>
          <coneGeometry args={[0.12, 0.18, 16]} />
          {glowingCyanConduit}
        </mesh>
      </group>
    </group>
  );
}
