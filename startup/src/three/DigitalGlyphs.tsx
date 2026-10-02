import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

interface DigitalGlyphsProps {
  visible?: boolean;
  count?: number;
}

export default function DigitalGlyphs({ visible = true, count = 24 }: DigitalGlyphsProps) {
  const groupRef = useRef<THREE.Group>(null);

  const glyphs = useMemo(() => {
    const data = [];
    const hexChars = '0123456789ABCDEF';
    
    for (let i = 0; i < count; i++) {
      const isBinary = Math.random() > 0.5;
      let text = '';
      if (isBinary) {
        text = Array.from({ length: 6 }, () => Math.random() > 0.5 ? '1' : '0').join('');
      } else {
        text = '0x' + Array.from({ length: 4 }, () => hexChars[Math.floor(Math.random() * 16)]).join('');
      }
      
      const u = Math.random();
      const v = Math.random();
      const theta = 2 * Math.PI * u;
      const phi = Math.acos(2 * v - 1);
      const radius = 4.8 + Math.random() * 1.5;
      
      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);
      
      data.push({
        text,
        position: [x, y, z] as [number, number, number],
        size: 0.14 + Math.random() * 0.08
      });
    }
    return data;
  }, [count]);

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.08 * delta;
      groupRef.current.rotation.x += 0.03 * delta;
    }
  });

  if (!visible) return null;

  return (
    <group ref={groupRef}>
      {glyphs.map((glyph, i) => (
        <Text
          key={i}
          position={glyph.position}
          fontSize={glyph.size}
          color="#00e5ff"
          anchorX="center"
          anchorY="middle"
          fillOpacity={0.6}
        >
          {glyph.text}
        </Text>
      ))}
    </group>
  );
}
