import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

// ─── Floating Ember Particles ───────────────────────────────────────────────
const EMBERS = Array.from({ length: 28 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  size: Math.random() * 3 + 1.5,
  delay: Math.random() * 8,
  duration: Math.random() * 8 + 10,
  drift: (Math.random() - 0.5) * 120,
  color: i % 3 === 0 ? '#E5A93C' : i % 3 === 1 ? '#E02F3E' : '#3CDCF0',
}));

export const FloatingEmbers: React.FC = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden">
    {EMBERS.map((e) => (
      <motion.span
        key={e.id}
        className="absolute bottom-0 rounded-full"
        style={{
          left: `${e.x}%`,
          width: e.size,
          height: e.size,
          background: e.color,
          boxShadow: `0 0 ${e.size * 3}px ${e.color}`,
        }}
        animate={{
          y: [0, -window.innerHeight - 100],
          x: [0, e.drift],
          opacity: [0, 0.9, 0.6, 0],
          scale: [1, 1.5, 0.5, 0],
        }}
        transition={{
          duration: e.duration,
          delay: e.delay,
          repeat: Infinity,
          ease: 'easeOut',
        }}
      />
    ))}
  </div>
);

// ─── Animated Grid Lines ─────────────────────────────────────────────────────
export const AnimatedGrid: React.FC<{ className?: string }> = ({ className }) => (
  <motion.div
    className={`pointer-events-none absolute inset-0 ${className ?? ''}`}
    style={{
      backgroundImage:
        'linear-gradient(rgba(229,169,60,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(229,169,60,0.06) 1px, transparent 1px)',
      backgroundSize: '46px 46px',
    }}
    animate={{ backgroundPosition: ['0px 0px', '46px 46px'] }}
    transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
  />
);

// ─── Binary Rain Column ───────────────────────────────────────────────────────
const CHARS = '01アイウエオカキクケコサシスセソ∑Σ∏∆';
function randomChars(n: number) {
  return Array.from({ length: n }, () => CHARS[Math.floor(Math.random() * CHARS.length)]).join('\n');
}

const COLS = Array.from({ length: 18 }, (_, i) => ({
  id: i,
  x: (i / 18) * 100 + Math.random() * 5,
  chars: randomChars(32),
  delay: Math.random() * 6,
  duration: Math.random() * 6 + 10,
  opacity: Math.random() * 0.18 + 0.04,
}));

export const BinaryRain: React.FC = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden select-none">
    {COLS.map((col) => (
      <motion.pre
        key={col.id}
        className="absolute top-0 font-mono text-[10px] leading-[1.45] whitespace-pre"
        style={{
          left: `${col.x}%`,
          color: '#3CDCF0',
          opacity: col.opacity,
          letterSpacing: '0.2em',
        }}
        animate={{ y: ['-100%', '120%'] }}
        transition={{
          duration: col.duration,
          delay: col.delay,
          repeat: Infinity,
          ease: 'linear',
        }}
      >
        {col.chars}
      </motion.pre>
    ))}
  </div>
);

// ─── Blood Moon Pulse ─────────────────────────────────────────────────────────
export const BloodMoonGlow: React.FC = () => (
  <motion.div
    className="pointer-events-none absolute top-[-10%] left-1/2 -translate-x-1/2"
    style={{ width: 600, height: 600 }}
    animate={{
      scale: [1, 1.12, 1],
      opacity: [0.35, 0.55, 0.35],
    }}
    transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
  >
    <div
      className="w-full h-full rounded-full"
      style={{
        background: 'radial-gradient(circle at 50% 50%, rgba(224,47,62,0.45) 0%, rgba(229,169,60,0.12) 40%, transparent 75%)',
        filter: 'blur(60px)',
      }}
    />
  </motion.div>
);

// ─── Scan Beam ───────────────────────────────────────────────────────────────
export const ScanBeam: React.FC = () => (
  <motion.div
    className="pointer-events-none absolute left-0 right-0"
    style={{
      height: '2px',
      background: 'linear-gradient(90deg, transparent, rgba(60,220,240,0.6), rgba(229,169,60,0.4), transparent)',
    }}
    animate={{ top: ['0%', '100%'], opacity: [0, 1, 1, 0] }}
    transition={{ duration: 4, repeat: Infinity, ease: 'linear', repeatDelay: 2 }}
  />
);

// ─── Canvas Particle System (WebGL-style dot stars) ───────────────────────────
export const StarField: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const stars = Array.from({ length: 120 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.2 + 0.3,
      a: Math.random(),
      da: (Math.random() - 0.5) * 0.008,
    }));

    let raf: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      stars.forEach((s) => {
        s.a += s.da;
        if (s.a <= 0 || s.a >= 1) s.da = -s.da;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(203,216,228,${s.a * 0.6})`;
        ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 w-full h-full"
    />
  );
};
