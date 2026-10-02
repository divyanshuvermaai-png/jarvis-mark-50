import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface PlasmaConduitsProps {
  visible?: boolean;
  intensity?: number;
  pulseSpeed?: number;
}

const conduitVertexShader = `
  varying vec2 vUv;
  varying vec3 vNormal;

  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const conduitFragmentShader = `
  uniform float uTime;
  uniform float uIntensity;
  varying vec2 vUv;
  varying vec3 vNormal;

  void main() {
    // Pulse wave rushing along the conduit towards the core (along U)
    float wave = fract(vUv.x * 2.5 - uTime * 1.8);
    float pulse = smoothstep(0.0, 0.4, wave) * smoothstep(1.0, 0.6, wave);

    // Color gradient: deep cyan base, brilliant white pulse peak
    vec3 baseColor = vec3(0.0, 0.35, 0.85);
    vec3 pulseColor = vec3(0.0, 0.95, 1.0);
    vec3 whiteHot = vec3(1.0, 1.0, 1.0);

    vec3 color = mix(baseColor, pulseColor, pulse);
    color = mix(color, whiteHot, pow(pulse, 3.0) * 0.8);

    // Fresnel rim glow across tube radius (along V)
    float rim = abs(vUv.y - 0.5) * 2.0;
    color += vec3(0.0, 0.8, 1.0) * pow(rim, 2.0) * 0.6;

    gl_FragColor = vec4(color * uIntensity, 0.85);
  }
`;

export default function PlasmaConduits({ visible = true, intensity = 1.0, pulseSpeed = 1.0 }: PlasmaConduitsProps) {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  // Generate 4 winding 3D bezier curves from the outer solenoids to the central core
  const tubeGeometries = useMemo(() => {
    const geometries: THREE.TubeGeometry[] = [];
    const solenoidPositions = [
      new THREE.Vector3(3.4, 0, 0),
      new THREE.Vector3(0, 0, 3.4),
      new THREE.Vector3(-3.4, 0, 0),
      new THREE.Vector3(0, 0, -3.4),
    ];

    solenoidPositions.forEach((start, i) => {
      // 3D waypoints routing through gantry toward core
      const midY = (i % 2 === 0 ? 1 : -1) * 1.2;
      const midAngle = (i / 4) * Math.PI * 2 + Math.PI / 8;
      const mid1 = new THREE.Vector3(
        Math.cos(midAngle) * 2.6,
        midY,
        Math.sin(midAngle) * 2.6
      );
      const mid2 = new THREE.Vector3(
        Math.cos(midAngle + 0.2) * 1.6,
        midY * 0.4,
        Math.sin(midAngle + 0.2) * 1.6
      );
      const end = new THREE.Vector3(0, midY * 0.1, 0);

      const curve = new THREE.CatmullRomCurve3([start, mid1, mid2, end]);
      geometries.push(new THREE.TubeGeometry(curve, 64, 0.055, 12, false));
    });

    return geometries;
  }, []);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uIntensity: { value: intensity },
    }),
    [intensity]
  );

  useFrame((state) => {
    if (matRef.current) {
      matRef.current.uniforms.uTime.value = state.clock.elapsedTime * pulseSpeed;
      matRef.current.uniforms.uIntensity.value = intensity;
    }
  });

  if (!visible) return null;

  return (
    <group>
      {tubeGeometries.map((geom, idx) => (
        <mesh key={idx} geometry={geom}>
          <shaderMaterial
            ref={idx === 0 ? matRef : undefined}
            vertexShader={conduitVertexShader}
            fragmentShader={conduitFragmentShader}
            uniforms={uniforms}
            transparent
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
}
