/**
 * WANO CTF — THE GRAND LINE COMMAND DECK
 *
 * An original, cinematic 3D procedural React Three Fiber environment:
 * - Giant glowing Crimson Blood Moon with volumetric atmospheric ring
 * - Dynamic ocean swells with cybernetic wireframe grid highlights
 * - Grand pirate galleon silhouette on the horizon with glowing golden mast lanterns
 * - Pirate captain silhouette standing on the quarterdeck overlooking the digital sea
 * - Distant misty Wano pagoda silhouettes on oceanic cliffs
 * - Floating fiery crimson embers and cyber optic particles
 * - Holographic nautical radar compass telemetry rings
 */
import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

export type SceneQuality = 'high' | 'low';

export interface HeroSceneProps {
  quality?: SceneQuality;
  className?: string;
}

const CRIMSON = '#E02F3E';
const CRIMSON_GLOW = '#FF4D5E';
const GOLD = '#E5A93C';
const OCEAN_BLUE = '#0D2138';
const OCEAN_DEEP = '#050B14';
const ACCENT = '#3CDCF0';

/* ------------------------------------------------------------------- textures */

function useGlowTexture(): THREE.Texture {
  return useMemo(() => {
    const size = 128;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
      gradient.addColorStop(0, 'rgba(255, 80, 90, 0.95)');
      gradient.addColorStop(0.35, 'rgba(224, 47, 62, 0.45)');
      gradient.addColorStop(0.7, 'rgba(229, 169, 60, 0.15)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, size, size);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }, []);
}

/* ---------------------------------------------------------------- blood moon */

const BloodMoon: React.FC<{ glow: THREE.Texture }> = ({ glow }) => {
  const moonRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Group>(null);

  useFrame((_state, delta) => {
    if (moonRef.current) {
      moonRef.current.rotation.y += delta * 0.02;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.015;
    }
  });

  return (
    <group position={[0, 4.5, -16]}>
      {/* Moon Sphere */}
      <mesh ref={moonRef}>
        <sphereGeometry args={[3.8, 32, 32]} />
        <meshBasicMaterial color={CRIMSON} />
      </mesh>

      {/* Atmospheric Halo Sprite */}
      <sprite scale={[14, 14, 1]}>
        <spriteMaterial map={glow} transparent opacity={0.85} blending={THREE.AdditiveBlending} />
      </sprite>

      {/* Holographic Radar Compass Ring around Moon */}
      <group ref={ringRef}>
        <mesh rotation={[0, 0, 0]}>
          <ringGeometry args={[4.4, 4.45, 64]} />
          <meshBasicMaterial color={GOLD} transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
        <mesh rotation={[0, 0, Math.PI / 4]}>
          <ringGeometry args={[4.8, 4.83, 32]} />
          <meshBasicMaterial color={ACCENT} transparent opacity={0.25} side={THREE.DoubleSide} />
        </mesh>
      </group>
    </group>
  );
};

/* ---------------------------------------------------------------- ocean waves */

const OceanSurface: React.FC = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  const wireRef = useRef<THREE.Mesh>(null);

  const { geometry } = useMemo(() => {
    const geo = new THREE.PlaneGeometry(36, 32, 48, 48);
    return { geometry: geo };
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime * 0.8;
    const pos = geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const u = pos.getX(i);
      const v = pos.getY(i);
      const z =
        Math.sin(u * 0.45 + t) * 0.35 +
        Math.cos(v * 0.35 + t * 1.2) * 0.28 +
        Math.sin((u + v) * 0.3 + t * 0.5) * 0.2;
      pos.setZ(i, z);
    }
    pos.needsUpdate = true;
  });

  return (
    <group position={[0, -1.8, -6]} rotation={[-Math.PI / 2.3, 0, 0]}>
      {/* Solid deep water plane */}
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          color={OCEAN_BLUE}
          roughness={0.15}
          metalness={0.85}
          emissive={OCEAN_DEEP}
        />
      </mesh>

      {/* Cybernetic Wireframe Grid on top */}
      <mesh ref={wireRef} geometry={geometry} position={[0, 0, 0.02]}>
        <meshBasicMaterial color={ACCENT} wireframe transparent opacity={0.12} />
      </mesh>
    </group>
  );
};

/* --------------------------------------------------------- galleon silhouette */

const PirateGalleonSilhouette: React.FC = () => {
  const shipRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (shipRef.current) {
      const t = state.clock.elapsedTime;
      // Gentle ocean rocking
      shipRef.current.rotation.z = Math.sin(t * 0.9) * 0.035;
      shipRef.current.rotation.x = Math.cos(t * 0.7) * 0.025;
      shipRef.current.position.y = -0.5 + Math.sin(t * 0.8) * 0.08;
    }
  });

  return (
    <group ref={shipRef} position={[3.6, -0.5, -9]} scale={[0.85, 0.85, 0.85]}>
      {/* Ship Hull Silhouette */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[4.2, 1.4, 1.8]} />
        <meshBasicMaterial color="#030609" />
      </mesh>
      {/* Raised Poop Deck / Quarterdeck */}
      <mesh position={[1.4, 0.7, 0]}>
        <boxGeometry args={[1.5, 0.9, 1.6]} />
        <meshBasicMaterial color="#020407" />
      </mesh>
      {/* Bowsprit */}
      <mesh position={[-2.4, 0.4, 0]} rotation={[0, 0, 0.35]}>
        <cylinderGeometry args={[0.06, 0.1, 1.8, 8]} />
        <meshBasicMaterial color="#020407" />
      </mesh>

      {/* Main Mast */}
      <mesh position={[0, 2.2, 0]}>
        <cylinderGeometry args={[0.07, 0.12, 3.8, 8]} />
        <meshBasicMaterial color="#020407" />
      </mesh>
      {/* Fore Mast */}
      <mesh position={[-1.3, 1.8, 0]}>
        <cylinderGeometry args={[0.06, 0.1, 3.2, 8]} />
        <meshBasicMaterial color="#020407" />
      </mesh>
      {/* Mizzen Mast */}
      <mesh position={[1.3, 1.6, 0]}>
        <cylinderGeometry args={[0.05, 0.09, 2.8, 8]} />
        <meshBasicMaterial color="#020407" />
      </mesh>

      {/* Billowing Main Sails (Curved planes) */}
      <mesh position={[0, 2.4, 0.05]} rotation={[0.1, 0, 0]}>
        <planeGeometry args={[2.2, 1.5, 8, 8]} />
        <meshBasicMaterial color="#020509" side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[-1.3, 2.0, 0.05]} rotation={[0.1, 0, 0]}>
        <planeGeometry args={[1.8, 1.3, 8, 8]} />
        <meshBasicMaterial color="#020509" side={THREE.DoubleSide} />
      </mesh>

      {/* Jolly Roger Skull Flag atop Main Mast */}
      <mesh position={[0.3, 4.0, 0]} rotation={[0, 0, 0]}>
        <planeGeometry args={[0.9, 0.5]} />
        <meshBasicMaterial color="#000000" side={THREE.DoubleSide} />
      </mesh>

      {/* Glowing Golden Lanterns */}
      <pointLight position={[2.1, 1.2, 0]} color={GOLD} intensity={4} distance={4} />
      <pointLight position={[-0.8, 1.8, 0.2]} color={GOLD} intensity={3} distance={3} />
      <mesh position={[2.1, 1.2, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshBasicMaterial color={GOLD} />
      </mesh>
    </group>
  );
};

/* ---------------------------------------------------- captain on deck foreground */

const CaptainSilhouette: React.FC = () => {
  const capRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (capRef.current) {
      const t = state.clock.elapsedTime;
      capRef.current.position.y = -1.1 + Math.sin(t * 0.7) * 0.03;
    }
  });

  return (
    <group ref={capRef} position={[-2.4, -1.1, -3.2]} scale={[0.65, 0.65, 0.65]}>
      {/* Ship Railing in foreground */}
      <mesh position={[0, 0.4, 0]}>
        <boxGeometry args={[3.2, 0.08, 0.08]} />
        <meshBasicMaterial color="#05090F" />
      </mesh>
      <mesh position={[-1.2, 0, 0]}>
        <boxGeometry args={[0.08, 0.8, 0.08]} />
        <meshBasicMaterial color="#05090F" />
      </mesh>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[0.08, 0.8, 0.08]} />
        <meshBasicMaterial color="#05090F" />
      </mesh>
      <mesh position={[1.2, 0, 0]}>
        <boxGeometry args={[0.08, 0.8, 0.08]} />
        <meshBasicMaterial color="#05090F" />
      </mesh>

      {/* Captain Figure Silhouette */}
      <group position={[0.2, 0.6, -0.2]}>
        {/* Legs / Boots */}
        <mesh position={[-0.14, 0.35, 0]}>
          <cylinderGeometry args={[0.07, 0.09, 0.7, 8]} />
          <meshBasicMaterial color="#020406" />
        </mesh>
        <mesh position={[0.14, 0.35, 0]}>
          <cylinderGeometry args={[0.07, 0.09, 0.7, 8]} />
          <meshBasicMaterial color="#020406" />
        </mesh>

        {/* Torso & Long Captain's Overcoat (flowing in wind) */}
        <mesh position={[0, 0.95, 0]}>
          <boxGeometry args={[0.38, 0.65, 0.22]} />
          <meshBasicMaterial color="#020406" />
        </mesh>
        {/* Flowing Coat Tails */}
        <mesh position={[0.22, 0.7, 0.15]} rotation={[0.2, 0.1, 0.3]}>
          <boxGeometry args={[0.45, 0.6, 0.05]} />
          <meshBasicMaterial color="#010305" />
        </mesh>

        {/* Head */}
        <mesh position={[0, 1.4, 0]}>
          <sphereGeometry args={[0.12, 12, 12]} />
          <meshBasicMaterial color="#020406" />
        </mesh>

        {/* Iconic Straw / Pirate Captain Hat Silhouette */}
        <mesh position={[0, 1.48, 0]} rotation={[0.1, 0, 0]}>
          <cylinderGeometry args={[0.32, 0.34, 0.04, 16]} />
          <meshBasicMaterial color="#010204" />
        </mesh>
        <mesh position={[0, 1.54, 0]}>
          <cylinderGeometry args={[0.14, 0.16, 0.12, 16]} />
          <meshBasicMaterial color="#010204" />
        </mesh>
      </group>
    </group>
  );
};

/* ---------------------------------------------------- floating embers & particles */

const GrandLineEmbers: React.FC<{ count?: number }> = ({ count = 90 }) => {
  const pointsRef = useRef<THREE.Points>(null);

  const { positions, velocities } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 1] = Math.random() * 9 - 2;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 16;

      vel[i * 3] = (Math.random() - 0.5) * 0.015;
      vel[i * 3 + 1] = Math.random() * 0.02 + 0.01; // drifting upward
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.015;
    }
    return { positions: pos, velocities: vel };
  }, [count]);

  useFrame(() => {
    if (!pointsRef.current) return;
    const pos = pointsRef.current.geometry.attributes.position;
    for (let i = 0; i < count; i++) {
      let y = pos.getY(i) + velocities[i * 3 + 1];
      let x = pos.getX(i) + velocities[i * 3];
      if (y > 8) y = -2;
      pos.setY(i, y);
      pos.setX(i, x);
    }
    pos.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.09}
        color={CRIMSON_GLOW}
        transparent
        opacity={0.85}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
};

/* ------------------------------------------------------------------- camera rig */

const CameraRig: React.FC = () => {
  const { camera, pointer } = useThree();
  useFrame(() => {
    // Subtle cinematic parallax with pointer
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, pointer.x * 0.8, 0.04);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, 1.2 + pointer.y * 0.4, 0.04);
    camera.lookAt(0, 1.8, -10);
  });
  return null;
};

/* ---------------------------------------------------------------- default scene */

const HeroScene: React.FC<HeroSceneProps> = ({ className }) => {
  const glow = useGlowTexture();

  return (
    <div className={className} aria-hidden="true">
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 1.2, 5], fov: 46, near: 0.1, far: 50 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <fogExp2 attach="fog" args={['#05070A', 0.05]} />
        <ambientLight intensity={0.4} color="#0D2138" />
        <directionalLight position={[0, 8, -12]} intensity={1.5} color={CRIMSON_GLOW} />
        <directionalLight position={[-4, 4, 2]} intensity={0.6} color={OCEAN_BLUE} />

        <BloodMoon glow={glow} />
        <OceanSurface />
        <PirateGalleonSilhouette />
        <CaptainSilhouette />
        <GrandLineEmbers count={110} />
        <CameraRig />
      </Canvas>
    </div>
  );
};

export default HeroScene;
