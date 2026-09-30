import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Link } from 'react-router-dom';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import {
  Swords,
  Flag,
  ArrowRight,
  RotateCcw,
  Compass,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  TERMINAL_SCRIPT,
  resolveCategoryIcon,
  EVENT_FALLBACK,
  splitDuration,
  pad,
  formatCount,
} from '../lib/warzone';
import {
  SectionShell,
  Reveal,
  LiveDot,
} from '../components/warzone/ui';
import {
  FloatingEmbers,
  BinaryRain,
  BloodMoonGlow,
  ScanBeam,
  StarField,
  AnimatedGrid,
} from '../components/warzone/AnimatedBg';

// Lazy-load 3D Grand Line Scene with Blood Moon, Galleon & Ocean
const HeroScene = lazy(() => import('../components/warzone/HeroScene'));

const GRAND_LINE_SECTORS = [
  { name: 'Web Security', island: 'Enies Lobby Port', slug: 'web', count: 6, points: 1250, desc: 'Bypass auth, SQLi, SSRF, IDOR & token forgery on marine web servers.' },
  { name: 'Cryptography', island: 'Poneglyph Vault', slug: 'crypto', count: 5, points: 1100, desc: 'Decipher ancient ciphers, break RSA, discrete logs & mathematical locks.' },
  { name: 'OSINT & Recon', island: 'Den Den Mushi Grid', slug: 'osint', count: 3, points: 650, desc: 'Intercept transponder signals, uncover hidden tracks & digital footprints.' },
  { name: 'Digital Forensics', island: 'Log Pose Artifacts', slug: 'forensics', count: 4, points: 950, desc: 'Analyze PCAP captures, memory dumps & corrupted sea charts.' },
  { name: 'Linux Bastion', island: 'Iron Kernel Citadel', slug: 'linux', count: 4, points: 800, desc: 'Root privilege escalation, suid binaries & stealth shellcraft.' },
  { name: 'Reverse Engineering', island: 'Vegapunk Circuits', slug: 'reverse', count: 5, points: 1400, desc: 'Decompile x86/ARM binaries, unpack malware & reverse algorithms.' },
  { name: 'Networking', island: 'All Blue Stream', slug: 'networking', count: 3, points: 750, desc: 'Packet routing triage, proxy pivoting & protocol exploitation.' },
  { name: 'Miscellaneous', island: 'Grand Line Anomalies', slug: 'misc', count: 4, points: 1200, desc: 'Steganography, esoteric bytecode & custom sea riddles.' },
];

/* ── Animated Counter ───────────────────────────────────────────────────── */
const AnimatedCounter: React.FC<{ to: number; prefix?: string; suffix?: string; className?: string }> = ({
  to, prefix = '', suffix = '', className,
}) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const duration = 1400;
    const step = Math.ceil(to / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= to) { setCount(to); clearInterval(timer); }
      else setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [to]);
  return <span className={className}>{prefix}{formatCount(count)}{suffix}</span>;
};

/* ── Stagger container ──────────────────────────────────────────────────── */
const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1, delayChildren: 0.2 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

export const Home: React.FC = () => {
  const { team, competition } = useAuth();

  // Terminal state
  const [scriptStep, setScriptStep] = useState(0);
  const [typedCommand, setTypedCommand] = useState('');

  // Countdown timer
  const [timeLeft, setTimeLeft] = useState<{ days: number; hours: number; minutes: number; seconds: number }>({
    days: 0, hours: 0, minutes: 0, seconds: 0,
  });

  // Mouse parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 30, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 30, damping: 20 });

  useEffect(() => {
    const move = (e: MouseEvent) => {
      const cx = window.innerWidth / 2, cy = window.innerHeight / 2;
      mouseX.set((e.clientX - cx) / cx * 14);
      mouseY.set((e.clientY - cy) / cy * 10);
    };
    window.addEventListener('mousemove', move);
    return () => window.removeEventListener('mousemove', move);
  }, [mouseX, mouseY]);

  useEffect(() => {
    const targetDate = new Date(competition?.start_at || EVENT_FALLBACK.dateIso).getTime();
    const updateCountdown = () => {
      const diff = Math.max(0, targetDate - Date.now());
      setTimeLeft(splitDuration(diff));
    };
    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [competition]);

  useEffect(() => {
    if (scriptStep >= TERMINAL_SCRIPT.length) return;
    const currentItem = TERMINAL_SCRIPT[scriptStep];
    let charIndex = 0;
    setTypedCommand('');
    const typeInterval = setInterval(() => {
      if (charIndex < currentItem.command.length) {
        setTypedCommand(currentItem.command.slice(0, charIndex + 1));
        charIndex++;
      } else {
        clearInterval(typeInterval);
        const timeout = setTimeout(() => setScriptStep((prev) => prev + 1), 1200);
        return () => clearTimeout(timeout);
      }
    }, 45);
    return () => clearInterval(typeInterval);
  }, [scriptStep]);

  const resetTerminal = () => { setScriptStep(0); setTypedCommand(''); };
  const isLive = competition?.status === 'live';

  return (
    <div className="relative overflow-hidden">

      {/* ══════════════════════════════ HERO SECTION ════════════════════════ */}
      <section
        className="relative min-h-[95vh] flex flex-col justify-center items-center px-4 pt-10 pb-20 border-b border-card-border/70 overflow-hidden"
        onMouseMove={(e) => {
          const cx = window.innerWidth / 2, cy = window.innerHeight / 2;
          mouseX.set((e.clientX - cx) / cx * 14);
          mouseY.set((e.clientY - cy) / cy * 10);
        }}
      >
        {/* Star field canvas */}
        <StarField />

        {/* 3D hero scene */}
        <div className="absolute inset-0 pointer-events-none opacity-55 z-0">
          <Suspense fallback={<div className="w-full h-full bg-background" />}>
            <HeroScene className="w-full h-full" />
          </Suspense>
        </div>

        {/* Animated ambient layers */}
        <BloodMoonGlow />
        <FloatingEmbers />
        <ScanBeam />
        <BinaryRain />

        {/* Atmospheric fog overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-void/40 via-void/55 to-background pointer-events-none z-10" />

        {/* Hero content with parallax */}
        <motion.div
          className="relative z-20 max-w-5xl mx-auto text-center"
          style={{ x: springX, y: springY }}
        >
          {/* Status Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-void/90 border border-gold/40 backdrop-blur-md mb-6 shadow-glow-gold"
          >
            <LiveDot label={isLive ? 'GRAND LINE OPERATION LIVE' : 'VOYAGE ON STANDBY'} tone={isLive ? 'green' : 'cyan'} />
            <span className="text-steel-600">|</span>
            <span className="font-mono text-[11px] text-gold font-bold tracking-widest uppercase flex items-center gap-1.5">
              <Compass className="h-3.5 w-3.5 text-gold" />
              <span>WANO FEST CYBER EXPEDITION</span>
            </span>
          </motion.div>

          {/* Logo with glow pulse */}
          <motion.div
            className="mb-6 flex justify-center"
            initial={{ opacity: 0, scale: 0.6, rotateY: -20 }}
            animate={{ opacity: 1, scale: 1, rotateY: 0 }}
            transition={{ duration: 0.9, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.img
              src="/logo.png"
              alt="CYBITRIDIC WANO FEST"
              className="h-28 sm:h-40 md:h-52 w-auto object-contain"
              style={{
                filter: 'drop-shadow(0 0 40px rgba(229,169,60,0.65))',
              }}
              animate={{
                filter: [
                  'drop-shadow(0 0 30px rgba(229,169,60,0.5))',
                  'drop-shadow(0 0 60px rgba(229,169,60,0.9))',
                  'drop-shadow(0 0 30px rgba(224,47,62,0.5))',
                  'drop-shadow(0 0 60px rgba(229,169,60,0.9))',
                  'drop-shadow(0 0 30px rgba(229,169,60,0.5))',
                ],
              }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              whileHover={{ scale: 1.06, rotate: [-1, 1, -1, 0] }}
            />
          </motion.div>

          {/* Hero Typography */}
          <motion.h1
            className="display-title text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white mb-4"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            ENTER THE{' '}
            <motion.span
              className="text-transparent bg-clip-text bg-gradient-to-r from-gold via-crimson to-accent inline-block"
              animate={{
                backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
              }}
              style={{ backgroundSize: '200% 200%' }}
              transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
            >
              GRAND LINE OF CYBERSECURITY
            </motion.span>
          </motion.h1>

          <motion.p
            className="text-base sm:text-xl text-steel-200 max-w-2xl mx-auto mb-10 leading-relaxed font-sans font-medium"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.55 }}
          >
            "Capture the Flag. Break the Code. Conquer the New World."
          </motion.p>

          {/* Hero CTAs */}
          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-5 mb-14"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.7 }}
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }}>
              <Link
                to="/challenges"
                className="hud-btn-gold w-full sm:w-auto px-10 py-4 text-sm font-extrabold flex items-center justify-center gap-3"
              >
                <Flag className="h-5 w-5 text-black" />
                <span>ENTER THE CTF</span>
                <ArrowRight className="h-4 w-4 text-black" />
              </Link>
            </motion.div>

            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }}>
              <Link
                to="/challenges"
                className="hud-btn-crimson w-full sm:w-auto px-10 py-4 text-sm font-extrabold flex items-center justify-center gap-3"
              >
                <Swords className="h-5 w-5 text-white" />
                <span>VIEW CHALLENGES</span>
              </Link>
            </motion.div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            className="flex flex-col items-center gap-2 text-steel-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.4 }}
          >
            <span className="font-mono text-[10px] tracking-widest uppercase">SCROLL TO EXPLORE</span>
            <motion.div
              className="w-px h-10 bg-gradient-to-b from-gold/60 to-transparent"
              animate={{ scaleY: [0, 1, 0], opacity: [0, 1, 0] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
            />
          </motion.div>
        </motion.div>
      </section>

      {/* ══════════════════════════ PLAYER DASHBOARD ════════════════════════ */}
      <section className="py-14 border-b border-card-border/70 bg-surface/45 relative overflow-hidden">
        <AnimatedGrid className="opacity-60" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <Reveal>
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <motion.span
                  className="h-px w-8 bg-gold/70"
                  animate={{ scaleX: [1, 1.6, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                <span className="label-hud text-gold">COMMAND DASHBOARD</span>
              </div>
              <span className="font-mono text-xs text-steel-400">TACTICAL TELEMETRY STREAM</span>
            </div>
          </Reveal>

          <motion.div
            className="grid grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-6"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
          >
            {/* Score */}
            <motion.div
              variants={fadeUp}
              whileHover={{ scale: 1.03, y: -4 }}
              className="p-5 rounded-2xl border border-gold/40 bg-void/80 relative overflow-hidden cursor-default"
              style={{ boxShadow: '0 0 30px -4px rgba(229,169,60,0.4)' }}
            >
              <motion.div
                className="absolute inset-0 rounded-2xl"
                animate={{ opacity: [0.05, 0.15, 0.05] }}
                transition={{ duration: 2.5, repeat: Infinity }}
                style={{ background: 'radial-gradient(circle at 50% 100%, rgba(229,169,60,0.3), transparent)' }}
              />
              <span className="label-hud text-gold block mb-2">⚔️ CURRENT SCORE</span>
              <div className="font-display font-black text-2xl sm:text-3xl text-gold font-mono">
                ฿ <AnimatedCounter to={team?.score || 350} />
              </div>
              <div className="mt-1 text-[11px] font-mono text-steel-400">Squad bounty accumulated</div>
            </motion.div>

            {/* Rank */}
            <motion.div
              variants={fadeUp}
              whileHover={{ scale: 1.03, y: -4 }}
              className="p-5 rounded-2xl border border-crimson/40 bg-void/80 relative overflow-hidden cursor-default"
              style={{ boxShadow: '0 0 30px -4px rgba(224,47,62,0.4)' }}
            >
              <motion.div
                className="absolute inset-0 rounded-2xl"
                animate={{ opacity: [0.05, 0.18, 0.05] }}
                transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
                style={{ background: 'radial-gradient(circle at 50% 100%, rgba(224,47,62,0.35), transparent)' }}
              />
              <span className="label-hud text-crimson block mb-2">🏴 GRAND LINE RANK</span>
              <div className="font-display font-black text-2xl sm:text-3xl font-mono" style={{ color: '#FF4D5E' }}>
                #{team ? (team.solved_count > 0 ? '03' : '—') : '12'}
              </div>
              <div className="mt-1 text-[11px] font-mono text-steel-400">Fleet standing position</div>
            </motion.div>

            {/* Targets */}
            <motion.div
              variants={fadeUp}
              whileHover={{ scale: 1.03, y: -4 }}
              className="p-5 rounded-2xl border border-accent/40 bg-void/80 relative overflow-hidden cursor-default"
              style={{ boxShadow: '0 0 30px -4px rgba(60,220,240,0.3)' }}
            >
              <motion.div
                className="absolute inset-0 rounded-2xl"
                animate={{ opacity: [0.04, 0.14, 0.04] }}
                transition={{ duration: 2.8, repeat: Infinity, delay: 1 }}
                style={{ background: 'radial-gradient(circle at 50% 100%, rgba(60,220,240,0.3), transparent)' }}
              />
              <span className="label-hud text-accent block mb-2">🧩 TARGETS CAPTURED</span>
              <div className="font-display font-black text-2xl sm:text-3xl text-accent font-mono">
                <AnimatedCounter to={team?.solved_count || 5} /> / 33
              </div>
              <div className="mt-1 text-[11px] font-mono text-steel-400">Islands liberated</div>
            </motion.div>

            {/* Pool */}
            <motion.div
              variants={fadeUp}
              whileHover={{ scale: 1.03, y: -4 }}
              className="p-5 rounded-2xl border border-cyber-green/40 bg-void/80 relative overflow-hidden cursor-default"
              style={{ boxShadow: '0 0 30px -4px rgba(47,211,164,0.3)' }}
            >
              <motion.div
                className="absolute inset-0 rounded-2xl"
                animate={{ opacity: [0.04, 0.14, 0.04] }}
                transition={{ duration: 3.2, repeat: Infinity, delay: 1.5 }}
                style={{ background: 'radial-gradient(circle at 50% 100%, rgba(47,211,164,0.28), transparent)' }}
              />
              <span className="label-hud text-cyber-green block mb-2">💰 TOTAL BOUNTY POOL</span>
              <div className="font-display font-black text-2xl sm:text-3xl text-cyber-green font-mono">
                <AnimatedCounter to={8500} /> <span className="text-xs text-steel-500">PTS</span>
              </div>
              <div className="mt-1 text-[11px] font-mono text-steel-400">Available across all islands</div>
            </motion.div>

            {/* Timer */}
            <motion.div
              variants={fadeUp}
              whileHover={{ scale: 1.03, y: -4 }}
              className="col-span-2 lg:col-span-1 p-5 rounded-2xl border border-card-border bg-void/80 relative overflow-hidden cursor-default"
            >
              <span className="label-hud text-steel-400 block mb-2">⏱️ TIME REMAINING</span>
              <div className="font-display font-black text-xl sm:text-2xl text-white font-mono flex items-center gap-1">
                <span>{pad(timeLeft.hours)}h</span>
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                >:</motion.span>
                <span>{pad(timeLeft.minutes)}m</span>
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                >:</motion.span>
                <motion.span
                  className="text-accent"
                  animate={{ opacity: [1, 0.4, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                >
                  {pad(timeLeft.seconds)}s
                </motion.span>
              </div>
              <div className="mt-1 text-[11px] font-mono text-steel-400">Until log pose freeze</div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════ GRAND LINE SECTORS ══════════════════════ */}
      <section className="py-20 px-4 max-w-7xl mx-auto relative">
        <SectionShell
          kicker="EXPEDITION SECTORS"
          title="THE GRAND LINE — TARGET ARCHIPELAGO"
          description="Navigate through eight high-security islands of the Grand Line. Each region holds classified flags guarded by real-world vulnerabilities."
          right={
            <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}>
              <Link to="/challenges" className="hud-btn-gold inline-flex items-center gap-2 self-start lg:self-auto text-xs">
                <span>OPEN FULL TREASURE MAP</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </motion.div>
          }
        >
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            {GRAND_LINE_SECTORS.map((sector, i) => {
              const Icon = resolveCategoryIcon(sector.slug, sector.slug);
              return (
                <motion.div
                  key={sector.slug}
                  variants={fadeUp}
                  whileHover={{
                    y: -8,
                    boxShadow: '0 0 30px -4px rgba(229,169,60,0.5)',
                    borderColor: 'rgba(229,169,60,0.6)',
                  }}
                  className="p-6 rounded-2xl border border-card-border/90 bg-surface/70 transition-colors duration-300 group cursor-pointer relative overflow-hidden"
                >
                  {/* shimmer on hover */}
                  <motion.div
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{
                      background: 'linear-gradient(135deg, rgba(229,169,60,0.06) 0%, transparent 60%)',
                    }}
                  />
                  <div className="flex items-center justify-between mb-4">
                    <motion.div
                      className="p-3 rounded-xl border border-gold/30 bg-gold/10 text-gold"
                      whileHover={{ scale: 1.2, rotate: 10 }}
                      transition={{ type: 'spring', stiffness: 300 }}
                    >
                      <Icon className="h-6 w-6" />
                    </motion.div>
                    <motion.span
                      className="font-mono text-xs font-bold text-accent px-2.5 py-0.5 rounded-full bg-void border border-card-border"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                    >
                      {sector.count} TARGETS
                    </motion.span>
                  </div>
                  <div className="label-hud text-crimson font-bold mb-1">{sector.island}</div>
                  <h4 className="font-display font-bold text-white text-lg mb-2 group-hover:text-gold transition-colors">{sector.name}</h4>
                  <p className="text-xs text-steel-400 mb-4 line-clamp-2 leading-relaxed">{sector.desc}</p>
                  <div className="flex items-center justify-between pt-3 border-t border-card-border/60 text-xs font-mono">
                    <span className="text-steel-400">Sector Bounty:</span>
                    <motion.span
                      className="font-bold text-gold"
                      animate={{ opacity: [0.8, 1, 0.8] }}
                      transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.15 }}
                    >
                      ฿ {sector.points}
                    </motion.span>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </SectionShell>
      </section>

      {/* ══════════════════════════ INTERACTIVE TERMINAL ════════════════════ */}
      <section className="py-16 px-4 max-w-6xl mx-auto">
        <Reveal>
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.span
                className="h-px w-8"
                style={{ background: 'rgba(224,47,62,0.7)' }}
                animate={{ scaleX: [1, 1.8, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <span className="label-hud text-crimson">EXPEDITION FLAG TRANSMISSION TERMINAL</span>
            </div>
            <motion.button
              onClick={resetTerminal}
              className="hud-btn-ghost py-1 px-3 text-xs flex items-center gap-1.5"
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.95 }}
              title="Replay console script"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>REPLAY TRANSMISSION</span>
            </motion.button>
          </div>

          <motion.div
            className="rounded-2xl border border-gold/40 bg-void/95 overflow-hidden font-mono text-xs sm:text-sm"
            style={{ boxShadow: '0 0 0 1px rgba(229,169,60,0.3), 0 20px 50px -15px rgba(0,0,0,0.9)' }}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            {/* Terminal Header */}
            <div className="bg-surface/90 px-4 py-3 border-b border-card-border flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {['crimson', 'gold', 'cyber-green'].map((c, i) => (
                  <motion.div
                    key={c}
                    className={`h-3 w-3 rounded-full`}
                    style={{ backgroundColor: i === 0 ? '#E02F3E' : i === 1 ? '#E5A93C' : '#2FD3A4' }}
                    animate={{ scale: [1, 1.2, 1], opacity: [0.8, 1, 0.8] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                  />
                ))}
                <span className="ml-2 text-steel-300 font-bold text-xs tracking-wider">
                  root@wano-ctf:~$ submit_flag --vessel STRAWH4T
                </span>
              </div>
              <motion.span
                className="label-hud text-gold"
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                DEN DEN MUSHI SECURED
              </motion.span>
            </div>

            {/* Terminal Body */}
            <div className="p-6 space-y-4 min-h-[260px] max-h-[380px] overflow-y-auto">
              {TERMINAL_SCRIPT.slice(0, scriptStep).map((item, idx) => (
                <motion.div
                  key={idx}
                  className="space-y-1"
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="flex items-center space-x-2 text-gold">
                    <motion.span
                      className="text-crimson font-bold"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >☠</motion.span>
                    <span className="text-white font-semibold">{item.command}</span>
                  </div>
                  {item.output.map((out, outIdx) => (
                    <motion.div
                      key={outIdx}
                      className="text-steel-300 pl-4 border-l border-gold/30"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: outIdx * 0.08 }}
                    >
                      {out.includes('flag accepted') ? (
                        <span className="text-cyber-green font-bold flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-cyber-green inline" />
                          <span>{out}</span>
                        </span>
                      ) : out.includes('vulnerability detected') ? (
                        <span className="text-gold font-semibold">{out}</span>
                      ) : out}
                    </motion.div>
                  ))}
                </motion.div>
              ))}

              {scriptStep < TERMINAL_SCRIPT.length && (
                <div className="space-y-1">
                  <div className="flex items-center space-x-2 text-gold">
                    <span className="text-crimson font-bold">☠</span>
                    <span className="text-white font-semibold">{typedCommand}</span>
                    <motion.span
                      className="h-4 w-2 bg-gold inline-block"
                      animate={{ opacity: [1, 0, 1] }}
                      transition={{ duration: 0.7, repeat: Infinity }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </Reveal>
      </section>

      {/* ══════════════════════════ BOTTOM CTA ══════════════════════════════ */}
      <section className="py-20 px-4 border-t border-card-border/70 bg-gradient-to-b from-void to-surface/50 relative overflow-hidden">
        <AnimatedGrid className="opacity-40" />
        <FloatingEmbers />
        <Reveal>
          <div className="max-w-4xl mx-auto text-center relative z-10">
            <motion.div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-gold/40 bg-gold/10 text-gold text-xs font-mono uppercase mb-4"
              animate={{ boxShadow: ['0 0 0 0 rgba(229,169,60,0)', '0 0 20px 4px rgba(229,169,60,0.3)', '0 0 0 0 rgba(229,169,60,0)'] }}
              transition={{ duration: 2.5, repeat: Infinity }}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>THE NEW WORLD AWAITS</span>
            </motion.div>

            <motion.h2
              className="display-title text-3xl sm:text-5xl text-white mb-4"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
            >
              SET SAIL WITH YOUR CREW
            </motion.h2>

            <motion.p
              className="text-base text-steel-300 max-w-xl mx-auto mb-8 font-sans"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              Ready your local tools, review the ancient directives, and claim your place among the greatest cyber pirates of the Grand Line.
            </motion.p>

            <motion.div
              className="flex flex-wrap items-center justify-center gap-4"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.35 }}
            >
              <motion.div whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.96 }}>
                <Link to="/register" className="hud-btn-gold px-8 py-3.5 text-xs font-bold flex items-center gap-2">
                  <span>ENROLL PIRATE SQUAD</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </motion.div>
              <motion.div whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.96 }}>
                <Link to="/rules" className="hud-btn-ghost px-8 py-3.5 text-xs flex items-center gap-2">
                  <span>RULES OF ENGAGEMENT</span>
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </Reveal>
      </section>
    </div>
  );
};
