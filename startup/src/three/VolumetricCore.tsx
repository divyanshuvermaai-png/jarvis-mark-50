import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface VolumetricCoreProps {
  intensity?: number;
  visible?: boolean;
  scale?: number;
}

// ── Plasma Vertex Shader: 3D Simplex Turbulence ──
const plasmaVertexShader = `
  uniform float uTime;
  uniform float uDisplacement;
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
  vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

  float snoise(vec3 v){ 
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);

    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + 1.0 * C.xxx;
    vec3 x2 = x0 - i2 + 2.0 * C.xxx;
    vec3 x3 = x0 - 1.0 + 3.0 * C.xxx;

    i = mod(i, 289.0); 
    vec4 p = permute(permute(permute( 
               i.z + vec4(0.0, i1.z, i2.z, 1.0))
             + i.y + vec4(0.0, i1.y, i2.y, 1.0)) 
             + i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 1.0/7.0;
    vec3 ns = n_ * D.wyz - D.xzx;

    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);

    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;

    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vUv = uv;
    
    // Multi-octave turbulence
    float n1 = snoise(position * 2.2 + uTime * 0.9);
    float n2 = snoise(position * 4.5 - uTime * 1.4) * 0.5;
    float displacement = (n1 + n2) * 0.12 * uDisplacement;
    vec3 newPosition = position + normal * displacement;
    
    vec4 worldPosition = modelMatrix * vec4(newPosition, 1.0);
    vPosition = worldPosition.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

// ── Plasma Fragment Shader: View-dependent Fresnel & Chromatic Rim ──
const plasmaFragmentShader = `
  uniform float uTime;
  uniform float uIntensity;
  
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  void main() {
    vec3 viewDirection = normalize(cameraPosition - vPosition);
    float fresnel = 1.0 - max(0.0, dot(viewDirection, vNormal));
    float fresnelCore = pow(fresnel, 2.4);
    
    // Tri-tone volumetric palette: deep space blue rim, electric cyan midtone, white-hot center
    vec3 rimColor = vec3(0.0, 0.2, 0.9);      // Deep blue
    vec3 midColor = vec3(0.0, 0.95, 1.0);     // Electric cyan
    vec3 centerColor = vec3(1.0, 1.0, 1.0);  // White hot

    vec3 plasma = mix(midColor, rimColor, fresnel);
    vec3 finalColor = mix(plasma, centerColor, (1.0 - fresnel) * 0.6 + fresnelCore * 0.4);

    // Dynamic core heartbeat pulsation
    float pulse = (sin(uTime * 4.5) * 0.5 + 0.5) * 0.3 + 0.85;
    
    gl_FragColor = vec4(finalColor * uIntensity * pulse, 0.92);
  }
`;

export default function VolumetricCore({ intensity = 1.0, visible = true, scale = 1.0 }: VolumetricCoreProps) {
  const plasmaMatRef = useRef<THREE.ShaderMaterial>(null);
  const latticeRef = useRef<THREE.Group>(null);
  const vortexRef = useRef<THREE.Points>(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uIntensity: { value: intensity },
      uDisplacement: { value: 1.0 },
    }),
    [intensity]
  );

  // Generate 600 particles for internal quantum vortex
  const [vortexPositions, vortexOriginalR] = useMemo(() => {
    const count = 600;
    const pos = new Float32Array(count * 3);
    const rad = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const r = 0.3 + Math.random() * 0.85;
      const theta = Math.random() * Math.PI * 2;
      const y = (Math.random() - 0.5) * 1.2;

      pos[i * 3] = Math.cos(theta) * r;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = Math.sin(theta) * r;
      rad[i] = r;
    }

    return [pos, rad];
  }, []);

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime;

    // Update GLSL Uniforms
    if (plasmaMatRef.current) {
      plasmaMatRef.current.uniforms.uTime.value = t;
      plasmaMatRef.current.uniforms.uIntensity.value = intensity;
    }

    // Rotate perforated containment lattice
    if (latticeRef.current) {
      latticeRef.current.rotation.y += 0.25 * delta;
      latticeRef.current.rotation.x -= 0.15 * delta;
    }

    // Animate Quantum Vortex Particles in logarithmic spiral
    if (vortexRef.current) {
      const positions = vortexRef.current.geometry.attributes.position.array as Float32Array;
      const count = positions.length / 3;

      for (let i = 0; i < count; i++) {
        let x = positions[i * 3];
        let y = positions[i * 3 + 1];
        let z = positions[i * 3 + 2];

        // Angular rotation around Y
        const currentAngle = Math.atan2(z, x) + (2.2 / (vortexOriginalR[i] + 0.2)) * delta;
        const r = vortexOriginalR[i];

        positions[i * 3] = Math.cos(currentAngle) * r;
        positions[i * 3 + 2] = Math.sin(currentAngle) * r;

        // Oscillating vertical drift
        y += Math.sin(t * 3.0 + i) * 0.005;
        if (y > 0.6) y = -0.6;
        if (y < -0.6) y = 0.6;
        positions[i * 3 + 1] = y;
      }
      vortexRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  if (!visible) return null;

  return (
    <group scale={scale}>
      {/* ── Layer 1: Inner White-Hot Crystalline Singularity Star ── */}
      <mesh>
        <icosahedronGeometry args={[0.45, 2]} />
        <meshBasicMaterial 
          color="#ffffff" 
          transparent 
          opacity={0.98} 
          blending={THREE.AdditiveBlending} 
        />
      </mesh>

      {/* ── Layer 2: Quantum Particle Vortex ── */}
      <points ref={vortexRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={vortexPositions.length / 3}
            array={vortexPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.045}
          color="#00e5ff"
          transparent
          opacity={0.85}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* ── Layer 3: Turbulent GLSL Plasma Shroud ── */}
      <mesh>
        <sphereGeometry args={[1.15, 36, 36]} />
        <shaderMaterial
          ref={plasmaMatRef}
          vertexShader={plasmaVertexShader}
          fragmentShader={plasmaFragmentShader}
          uniforms={uniforms}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* ── Layer 4: Perforated Magnetic Containment Lattice Shell ── */}
      <group ref={latticeRef}>
        <mesh>
          <icosahedronGeometry args={[1.35, 1]} />
          <meshStandardMaterial
            color="#001830"
            emissive="#00e5ff"
            emissiveIntensity={0.6 * intensity}
            wireframe
            transparent
            opacity={0.4}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      </group>

      {/* ── Layer 5: Volumetric Outward Corona Glow ── */}
      <mesh>
        <sphereGeometry args={[1.65, 16, 16]} />
        <meshBasicMaterial 
          color="#0077ff" 
          transparent 
          opacity={0.15 * intensity} 
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}
