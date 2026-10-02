import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Billboard } from '@react-three/drei';
import * as THREE from 'three';

interface HoloPanelsProps {
  visible?: boolean;
  dockProgress?: number; // 0 to 1
  scanned?: boolean; // true once system scan has passed
  currentScanY?: number;
}

export default function HoloPanels({ 
  visible = true, 
  dockProgress = 1.0, 
  scanned = false,
  currentScanY = 0 
}: HoloPanelsProps) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.08 * delta;
    }
  });

  if (!visible || dockProgress <= 0.05) return null;

  const panelsData = [
    { title: 'NEURAL CORE', initStatus: 'SYNCING...', readyStatus: 'READY // SYNCHRONIZED', y: 1.8, angle: 0 },
    { title: 'COGNITIVE ENGINE', initStatus: 'INITIALIZING...', readyStatus: 'READY // OPTIMAL', y: -1.4, angle: Math.PI / 2 },
    { title: 'MEMORY MATRIX', initStatus: 'ALLOCATING...', readyStatus: '32 GB UNIFIED // READY', y: 1.2, angle: Math.PI },
    { title: 'PERCEPTION LAYER', initStatus: 'STANDBY...', readyStatus: 'ONLINE // 100%', y: -1.7, angle: Math.PI * 1.5 },
  ];

  const currentRadius = 4.4 * Math.min(dockProgress, 1.0);

  return (
    <group ref={groupRef}>
      {panelsData.map((panel, idx) => {
        const x = Math.cos(panel.angle) * currentRadius;
        const z = Math.sin(panel.angle) * currentRadius;

        // Check if the scan beam is currently passing this panel
        const isNearScan = Math.abs(currentScanY - panel.y) < 1.0;
        const isReady = scanned || isNearScan;

        return (
          <group 
            key={idx} 
            position={[x, panel.y * dockProgress, z]} 
            scale={[dockProgress, dockProgress, dockProgress]}
          >
            <Billboard follow={true}>
              {/* Glass Holographic Backing */}
              <mesh>
                <planeGeometry args={[2.4, 0.8]} />
                <meshBasicMaterial 
                  color={isNearScan ? "#002850" : "#001224"} 
                  transparent 
                  opacity={isNearScan ? 0.85 : 0.55} 
                  side={THREE.DoubleSide} 
                />
              </mesh>

              {/* Glowing Corner Accents */}
              <lineSegments>
                <edgesGeometry args={[new THREE.PlaneGeometry(2.4, 0.8)]} />
                <lineBasicMaterial 
                  color={isNearScan ? "#ffffff" : "#00e5ff"} 
                  transparent 
                  opacity={isNearScan ? 0.95 : 0.65} 
                />
              </lineSegments>

              {/* Section Header Title */}
              <Text
                position={[0, 0.16, 0.04]}
                fontSize={0.11}
                color="#00e5ff"
                anchorX="center"
                anchorY="middle"
              >
                {panel.title}
              </Text>

              {/* Dynamic Telemetry Status */}
              <Text
                position={[0, -0.12, 0.04]}
                fontSize={0.095}
                color={isReady ? "#00ff88" : "#00a8ff"}
                anchorX="center"
                anchorY="middle"
              >
                {isReady ? panel.readyStatus : panel.initStatus}
              </Text>
            </Billboard>
          </group>
        );
      })}
    </group>
  );
}
