import React from 'react';
import { animate, motion, useReducedMotion } from 'framer-motion';
import { cn } from '../../lib/cn';
import { difficultyMeta, formatCount } from '../../lib/warzone';

/** Shared cinematic easing so every surface moves with the same weight. */
export const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* --------------------------------------------------------------------- reveal */

interface RevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
}

/** Holographic panels fading up as they enter the viewport (once). */
export const Reveal: React.FC<RevealProps> = ({ children, className, delay = 0, y = 26 }) => {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-70px' }}
      transition={{ duration: 0.75, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
};

/* ----------------------------------------------------------------- hud frames */

interface HudFrameProps extends React.HTMLAttributes<HTMLDivElement> {
  sm?: boolean;
  interactive?: boolean;
  tone?: 'blue' | 'cyan' | 'alert';
}

/** The glass command panel used by every screen in the console. */
export const HudFrame: React.FC<HudFrameProps> = ({
  sm = false,
  interactive = false,
  tone = 'blue',
  className,
  children,
  ...rest
}) => (
  <div
    className={cn(
      sm ? 'hud-panel-sm' : 'hud-panel',
      'hud-sheen hud-topline',
      interactive &&
        'transition-all duration-500 ease-cinema hover:-translate-y-1 hover:border-accent/40 hover:shadow-hud-hover',
      className
    )}
    {...rest}
  >
    <span
      aria-hidden
      className={cn(
        'pointer-events-none absolute inset-0',
        tone === 'cyan' && 'bg-accent/[0.035]',
        tone === 'alert' && 'bg-alert/[0.05]'
      )}
    />
    {children}
  </div>
);

export const PanelHeader: React.FC<{
  kicker: string;
  title: string;
  right?: React.ReactNode;
  className?: string;
}> = ({ kicker, title, right, className }) => (
  <div className={cn('flex items-start justify-between gap-4', className)}>
    <div>
      <div className="label-hud text-accent/90">{kicker}</div>
      <h3 className="mt-1 font-display text-base font-bold uppercase tracking-ops text-white sm:text-lg">
        {title}
      </h3>
    </div>
    {right}
  </div>
);

/* ------------------------------------------------------------- section shell */

interface SectionShellProps {
  id?: string;
  kicker: string;
  title: string;
  description?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SectionShell: React.FC<SectionShellProps> = ({
  id,
  kicker,
  title,
  description,
  right,
  children,
  className,
}) => (
  <section
    id={id}
    className={cn('relative mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8', className)}
  >
    <Reveal>
      <header className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="mb-3 flex items-center gap-3">
            <span aria-hidden className="h-px w-8 bg-accent/70" />
            <span className="label-hud text-accent">{kicker}</span>
          </div>
          <h2 className="display-title text-3xl leading-[1.06] sm:text-4xl lg:text-[2.55rem]">{title}</h2>
          {description ? (
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-steel-300 sm:text-base">
              {description}
            </p>
          ) : null}
        </div>
        {right}
      </header>
      <div className="hair-line mb-10" />
    </Reveal>
    {children}
  </section>
);
/* ------------------------------------------------------------ animated number */

export const AnimatedNumber: React.FC<{
  value: number;
  className?: string;
  duration?: number;
}> = ({ value, className, duration = 0.9 }) => {
  const ref = React.useRef<HTMLSpanElement>(null);
  const previous = React.useRef(0);

  React.useEffect(() => {
    const from = previous.current;
    previous.current = value;
    const node = ref.current;
    if (!node) return;
    if (from === value) {
      node.textContent = formatCount(value);
      return;
    }
    const controls = animate(from, value, {
      duration,
      ease: 'easeOut',
      onUpdate: (latest) => {
        node.textContent = formatCount(latest);
      },
    });
    return () => controls.stop();
  }, [value, duration]);

  return (
    <span ref={ref} className={className}>
      {formatCount(value)}
    </span>
  );
};

/* -------------------------------------------------------------- status atoms */

export const ThreatPips: React.FC<{
  difficulty?: string | null;
  showLabel?: boolean;
  className?: string;
}> = ({ difficulty, showLabel = true, className }) => {
  const meta = difficultyMeta(difficulty);
  return (
    <span
      className={cn('inline-flex items-center gap-2', className)}
      title={`Threat assessment: ${meta.label}`}
    >
      <span className="flex items-end gap-[3px]" aria-hidden>
        {[0, 1, 2, 3].map((index) => (
          <span
            key={index}
            className={cn(
              'h-3 w-[3px] rounded-sm transition-colors duration-300',
              index < meta.pips ? meta.bar : 'bg-steel-700'
            )}
          />
        ))}
      </span>
      {showLabel ? (
        <span className={cn('font-mono text-[10px] font-bold uppercase tracking-ops', meta.text)}>
          {meta.label}
        </span>
      ) : null}
    </span>
  );
};

const STATUS_META: Record<string, { label: string; led: string; shell: string }> = {
  live: {
    label: 'LIVE',
    led: 'led-live',
    shell: 'border-cyber-green/35 bg-cyber-green/[0.08] text-cyber-green',
  },
  upcoming: {
    label: 'STANDBY',
    led: 'led-idle',
    shell: 'border-accent/35 bg-accent/[0.08] text-accent',
  },
  paused: {
    label: 'PAUSED',
    led: 'led-idle',
    shell: 'border-cyber-yellow/35 bg-cyber-yellow/[0.08] text-cyber-yellow',
  },
  ended: {
    label: 'COMPLETE',
    led: 'led-idle',
    shell: 'border-line bg-void/60 text-steel-300',
  },
};

export const StatusPill: React.FC<{ status?: string | null; label?: string; className?: string }> = ({
  status,
  label,
  className,
}) => {
  const key = (status ?? 'upcoming').toLowerCase();
  const meta = STATUS_META[key] ?? STATUS_META.upcoming;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-ops',
        meta.shell,
        className
      )}
    >
      <span className={cn(meta.led, key === 'live' && 'animate-pulse')} />
      {label ?? meta.label}
    </span>
  );
};
export const LiveDot: React.FC<{ label: string; className?: string; tone?: 'green' | 'cyan' }> = ({
  label,
  className,
  tone = 'green',
}) => (
  <span className={cn('inline-flex items-center gap-2', className)}>
    <span className="relative flex h-2 w-2" aria-hidden>
      <span
        className={cn(
          'absolute inset-0 animate-pulse-ring rounded-full',
          tone === 'green' ? 'bg-cyber-green/60' : 'bg-accent/60'
        )}
      />
      <span
        className={cn('relative h-2 w-2 rounded-full', tone === 'green' ? 'bg-cyber-green' : 'bg-accent')}
      />
    </span>
    <span className="font-mono text-[10px] font-semibold uppercase tracking-ops text-steel-300">
      {label}
    </span>
  </span>
);

/* -------------------------------------------------------------- hud readouts */

export const MetricCard: React.FC<{
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  tone?: 'blue' | 'cyan' | 'alert';
  className?: string;
}> = ({ label, value, hint, icon: Icon, tone = 'blue', className }) => (
  <HudFrame sm tone={tone} interactive className={cn('bracket p-5', className)}>
    <div className="relative flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="label-hud">{label}</div>
        <div className="mt-2 truncate font-display text-lg font-bold uppercase text-white sm:text-xl">
          {value}
        </div>
        {hint ? <div className="mt-1 font-mono text-[11px] text-steel-400">{hint}</div> : null}
      </div>
      {Icon ? (
        <span
          className={cn(
            'shrink-0 rounded-lg border p-2 transition-colors duration-500',
            tone === 'cyan'
              ? 'border-accent/30 bg-accent/10 text-accent'
              : tone === 'alert'
                ? 'border-alert/30 bg-alert/10 text-alert-soft'
                : 'border-primary/30 bg-primary/10 text-primary-glow'
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
      ) : null}
    </div>
  </HudFrame>
);

/* ------------------------------------------------------------ decorative bits */

/** Seamless scrolling hex/binary gutter column. */
export const DataStream: React.FC<{ className?: string; seed?: number; lines?: number }> = ({
  className,
  seed = 7,
  lines = 26,
}) => {
  const reduce = useReducedMotion();
  const text = React.useMemo(() => {
    let state = seed * 9301 + 49297;
    const next = () => {
      state = (state * 9301 + 49297) % 233280;
      return state / 233280;
    };
    return Array.from({ length: lines }, () => {
      const hex = Math.floor(next() * 65535)
        .toString(16)
        .toUpperCase()
        .padStart(4, '0');
      const bin = Math.floor(next() * 255)
        .toString(2)
        .padStart(8, '0');
      return `${hex} ${bin}`;
    }).join('\n');
  }, [lines, seed]);

  return (
    <div aria-hidden className={cn('pointer-events-none select-none overflow-hidden', className)}>
      <div className={cn('stream-col mask-fade-y', !reduce && 'animate-stream')}>
        <div>{text}</div>
        <div>{text}</div>
      </div>
    </div>
  );
};

/** Thin optic beam that sweeps a panel. Decorative only. */
export const ScanBeam: React.FC<{ className?: string }> = ({ className }) => {
  const reduce = useReducedMotion();
  if (reduce) return null;
  return <span aria-hidden className={cn('optic-beam animate-sweep', className)} />;
};

export const HudDivider: React.FC<{ label?: string; className?: string }> = ({ label, className }) => (
  <div className={cn('flex items-center gap-3', className)}>
    <span
      aria-hidden
      className="h-px flex-1 bg-gradient-to-r from-transparent via-primary/35 to-transparent"
    />
    {label ? <span className="label-hud whitespace-nowrap">{label}</span> : null}
    <span
      aria-hidden
      className="h-px flex-1 bg-gradient-to-r from-transparent via-primary/35 to-transparent"
    />
  </div>
);


