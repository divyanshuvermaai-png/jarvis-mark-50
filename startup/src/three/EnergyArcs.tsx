import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { AudioSync } from '../audio/AudioSync';

interface EnergyArcsProps {
  visible?: boolean;
  intensity?: number;
  phase?: string;
  audioSync?: AudioSync | null;
}

export default function EnergyArcs({
  visible = true,
  intensity = 1.0,
  phase,
  audioSync,
}: EnergyArcsProps) {
  const groupRef = useRef<THREE.Group>(null);
  const numArcs = 10;
  const pointsPerArc = 14;

  // Pre-allocate 10 lightning arc geometries connected to the 10 solenoids (R = 2.16)
  const arcs = useMemo(() => {
    return Array.from({ length: numArcs }, (_, i) => {
      const angle = (i / numArcs) * Math.PI * 2;
      const start = new THREE.Vector3(Math.cos(angle) * 2.16, Math.sin(angle) * 2.16, 0.2);
      const end = new THREE.Vector3(Math.cos(angle) * 0.4, Math.sin(angle) * 0.4, 0.05);

      const positions = new Float32Array(pointsPerArc * 3);
      const geom = new THREE.BufferGeometry();
      geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      const mat = new THREE.LineBasicMaterial({
        color: new THREE.Color(i % 2 === 0 ? '#00f5ff' : '#ffffff'),
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        linewidth: 1.5,
      });

      return { start, end, geom, mat, angle };
    });
  }, []);

  useFrame((state) => {
    if (!visible || phase === 'collapse') return;
    const time = state.clock.elapsedTime;

    // Sample real-time audio energy
    let audioPeak = 0;
    let audioRms = 0;
    if (audioSync) {
      const energy = audioSync.getEnergy();
      audioPeak = energy.peak;
      audioRms = energy.rms;
    }

    arcs.forEach((arc, i) => {
      const posAttr = arc.geom.getAttribute('position') as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;

      // Electric arc activity varies on phase and audio transients
      const isActive = phase === 'scanning' || phase === 'synchronization' || phase === 'activation';
      const baseJitter = (isActive ? 0.35 : 0.12) + audioPeak * 0.35;

      for (let j = 0; j < pointsPerArc; j++) {
        const t = j / (pointsPerArc - 1);
        const lerpX = THREE.MathUtils.lerp(arc.end.x, arc.start.x, t);
        const lerpY = THREE.MathUtils.lerp(arc.end.y, arc.start.y, t);
        const lerpZ = THREE.MathUtils.lerp(arc.end.z, arc.start.z, t);

        // High-frequency jitter at the middle of the lightning arc
        const midFalloff = Math.sin(t * Math.PI);
        const jitterX = (Math.random() - 0.5) * baseJitter * midFalloff;
        const jitterY = (Math.random() - 0.5) * baseJitter * midFalloff;
        const jitterZ = (Math.random() - 0.5) * (baseJitter * 0.5) * midFalloff;

        arr[j * 3] = lerpX + jitterX;
        arr[j * 3 + 1] = lerpY + jitterY;
        arr[j * 3 + 2] = lerpZ + jitterZ;
      }

      posAttr.needsUpdate = true;

      // Rapid electrical strobe flicker reacting to audio
      const strobe = Math.sin(time * 30.0 + i * 1.5) > 0.1 ? 0.75 : 0.2;
      arc.mat.opacity = Math.min(1.0, (strobe * intensity * (isActive ? 1.0 : 0.3)) + audioRms * 0.5);
    });
  });

  if (!visible || phase === 'collapse') return null;

  return (
    <group ref={groupRef}>
      {arcs.map((arc, i) => (
        <primitive key={`arc-${i}`} object={new THREE.Line(arc.geom, arc.mat)} />
      ))}
    </group>
  );
}
