import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface InternalMachineryProps {
  visible?: boolean;
  scale?: number;
  highlightY?: number; // Y-coord for spatial scan illumination
}

export default function InternalMachinery({ visible = true, scale = 1.0, highlightY = 0 }: InternalMachineryProps) {
  const rotorShaftRef = useRef<THREE.Group>(null);
  const statorVanesRef = useRef<THREE.Group>(null);
  const gimbalRingRef = useRef<THREE.Group>(null);
  const radiatorTopRef = useRef<THREE.Group>(null);
  const radiatorBottomRef = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    // 1. Axial rotor shaft rotates steadily
    if (rotorShaftRef.current) {
      rotorShaftRef.current.rotation.y += 0.45 * delta;
    }

    // 2. Stator aerofoil vanes counter-rotate at independent speed
    if (statorVanesRef.current) {
      statorVanesRef.current.rotation.y -= 0.28 * delta;
    }

    // 3. Gyroscopic gimbal tilts and precesses
    if (gimbalRingRef.current) {
      gimbalRingRef.current.rotation.z += 0.18 * delta;
      gimbalRingRef.current.rotation.x += 0.12 * delta;
    }

    // 4. Subtle pulsating expansion on radiator heat-sink fins
    const t = state.clock.elapsedTime;
    const pulse = 1.0 + Math.sin(t * 3.0) * 0.03;
    if (radiatorTopRef.current) radiatorTopRef.current.scale.set(pulse, 1, pulse);
    if (radiatorBottomRef.current) radiatorBottomRef.current.scale.set(pulse, 1, pulse);
  });

  if (!visible) return null;

  const machineMetalMaterial = (
    <meshStandardMaterial
      color="#021020"
      emissive="#00b4d8"
      emissiveIntensity={0.55}
      metalness={0.88}
      roughness={0.22}
      transparent
      opacity={0.88}
    />
  );

  const glowingConduitMaterial = (
    <meshBasicMaterial
      color="#00e5ff"
      transparent
      opacity={0.9}
      blending={THREE.AdditiveBlending}
    />
  );

  return (
    <group scale={scale}>
      {/* ── 1. Central Axial Drive Shaft & Mechanical Collar Bearings ── */}
      <group ref={rotorShaftRef}>
        {/* Central Cylindrical Spindle */}
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[0.22, 0.22, 4.4, 24]} />
          {machineMetalMaterial}
        </mesh>

        {/* Upper & Lower Bearing Collar Mounts */}
        <mesh position={[0, 1.85, 0]}>
          <cylinderGeometry args={[0.38, 0.38, 0.25, 16]} />
          {machineMetalMaterial}
        </mesh>
        <mesh position={[0, -1.85, 0]}>
          <cylinderGeometry args={[0.38, 0.38, 0.25, 16]} />
          {machineMetalMaterial}
        </mesh>

        {/* Notched Gear Teeth around Central Hub */}
        {Array.from({ length: 8 }).map((_, i) => {
          const angle = (i / 8) * Math.PI * 2;
          return (
            <mesh key={i} position={[Math.cos(angle) * 0.4, 0, Math.sin(angle) * 0.4]}>
              <boxGeometry args={[0.08, 0.4, 0.08]} />
              {glowingConduitMaterial}
            </mesh>
          );
        })}
      </group>

      {/* ── 2. Twelve Stator Aerofoil Vanes (Angled at 45° around Core) ── */}
      <group ref={statorVanesRef}>
        {Array.from({ length: 12 }).map((_, i) => {
          const angle = (i / 12) * Math.PI * 2;
          const r = 2.1;
          const x = Math.cos(angle) * r;
          const z = Math.sin(angle) * r;

          return (
            <group key={i} position={[x, 0, z]} rotation={[0, -angle + Math.PI / 4, 0]}>
              {/* Thick 3D Aerodynamic Vane Blade */}
              <mesh>
                <boxGeometry args={[0.55, 0.95, 0.06]} />
                {machineMetalMaterial}
              </mesh>
              {/* Luminous Edge Line */}
              <mesh position={[0.26, 0, 0]}>
                <boxGeometry args={[0.03, 0.95, 0.07]} />
                {glowingConduitMaterial}
              </mesh>
            </group>
          );
        })}
      </group>

      {/* ── 3. Gyroscopic Gimbal Stabilizer Ring ── */}
      <group ref={gimbalRingRef} rotation={[THREE.MathUtils.degToRad(25), 0, 0]}>
        <mesh>
          <torusGeometry args={[2.75, 0.045, 16, 64]} />
          {machineMetalMaterial}
        </mesh>
        {/* Gimbal Mounting Pivots at 4 Quadrants */}
        {[0, Math.PI / 2, Math.PI, Math.PI * 1.5].map((angle, i) => (
          <mesh key={i} position={[Math.cos(angle) * 2.75, 0, Math.sin(angle) * 2.75]}>
            <sphereGeometry args={[0.09, 12, 12]} />
            {glowingConduitMaterial}
          </mesh>
        ))}
      </group>

      {/* ── 4. Interlocking Radiator Heat-Sink Fin Stacks (Upper & Lower) ── */}
      <group ref={radiatorTopRef} position={[0, 1.45, 0]}>
        {[0.12, 0.28, 0.44].map((yOffset, i) => (
          <mesh key={i} position={[0, yOffset, 0]}>
            <cylinderGeometry args={[1.1 - i * 0.15, 1.1 - i * 0.15, 0.04, 24]} />
            {machineMetalMaterial}
          </mesh>
        ))}
      </group>

      <group ref={radiatorBottomRef} position={[0, -1.45, 0]}>
        {[-0.12, -0.28, -0.44].map((yOffset, i) => (
          <mesh key={i} position={[0, yOffset, 0]}>
            <cylinderGeometry args={[1.1 - i * 0.15, 1.1 - i * 0.15, 0.04, 24]} />
            {machineMetalMaterial}
          </mesh>
        ))}
      </group>

      {/* ── 5. Asymmetrical Sensor Pods & Optical Emitters ── */}
      {/* Heavy diagnostic sensor mounted at 35° azimuth */}
      <group position={[Math.cos(0.6) * 2.9, 0.45, Math.sin(0.6) * 2.9]}>
        <mesh>
          <boxGeometry args={[0.3, 0.45, 0.25]} />
          {machineMetalMaterial}
        </mesh>
        <mesh position={[0, 0, 0.14]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.06, 0.06, 0.05, 16]} />
          {glowingConduitMaterial}
        </mesh>
      </group>

      {/* Secondary sensor cluster mounted at 210° azimuth */}
      <group position={[Math.cos(3.6) * 2.85, -0.55, Math.sin(3.6) * 2.85]}>
        <mesh>
          <boxGeometry args={[0.22, 0.35, 0.22]} />
          {machineMetalMaterial}
        </mesh>
        <mesh position={[0, 0, 0.12]}>
          <sphereGeometry args={[0.06, 12, 12]} />
          {glowingConduitMaterial}
        </mesh>
      </group>
    </group>
  );
}
