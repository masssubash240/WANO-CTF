/**
 * WANO CTF — shared content + presentation metadata.
 *
 * Everything the marketing/console surfaces need that is not served by the API:
 * category iconography, difficulty grading, rules, about copy, terminal script
 * and the formatting helpers used across the HUD.
 */
import {
  Binary,
  Cpu,
  Github,
  Globe,
  Instagram,
  KeyRound,
  Linkedin,
  Mail,
  MessageCircle,
  Network,
  Puzzle,
  Radar,
  Search,
  Terminal,
  Twitter,
  type LucideIcon,
} from 'lucide-react';

/* ------------------------------------------------------------------ identity */

export const SITE = {
  name: 'WANO CTF',
  tagline: 'ENTER THE DIGITAL WARZONE',
  subtitle: 'Break. Exploit. Capture. Defend.',
  org: 'WANO Fest Cyber Ops',
  url: 'https://ctf.wano-fest.com',
  supportEmail: 'cyberops@wano-fest.com',
} as const;

export const NAV_LINKS = [
  { label: 'HOME', to: '/' },
  { label: 'CHALLENGES', to: '/challenges' },
  { label: 'RULES', to: '/rules' },
  { label: 'LEADERBOARD', to: '/scoreboard' },
  { label: 'TEAMS', to: '/teams' },
  { label: 'ABOUT', to: '/about' },
] as const;

export const SOCIAL_LINKS = [
  { label: 'X / Twitter', href: 'https://x.com/wanofest', icon: Twitter },
  { label: 'GitHub', href: 'https://github.com/wano-fest', icon: Github },
  { label: 'LinkedIn', href: 'https://www.linkedin.com/company/wano-fest', icon: Linkedin },
  { label: 'Instagram', href: 'https://www.instagram.com/wano_fest', icon: Instagram },
  { label: 'Community', href: 'https://ctf.wano-fest.com/', icon: MessageCircle },
  { label: 'Email the organisers', href: `mailto:${SITE.supportEmail}`, icon: Mail },
] as const;

/* -------------------------------------------------------------- category icons */

/** The backend stores the Lucide icon name on each category (e.g. "Globe"). */
const ICON_BY_NAME: Record<string, LucideIcon> = {
  globe: Globe,
  keyround: KeyRound,
  search: Search,
  radar: Radar,
  terminal: Terminal,
  binary: Binary,
  network: Network,
  puzzle: Puzzle,
  cpu: Cpu,
};

const ICON_BY_SLUG: Record<string, LucideIcon> = {
  web: Globe,
  crypto: KeyRound,
  forensics: Search,
  osint: Radar,
  linux: Terminal,
  reverse: Binary,
  networking: Network,
  misc: Puzzle,
};

export function resolveCategoryIcon(icon?: string | null, slug?: string | null): LucideIcon {
  const byName = icon ? ICON_BY_NAME[icon.toLowerCase().replace(/[^a-z]/g, '')] : undefined;
  if (byName) return byName;
  const bySlug = slug ? ICON_BY_SLUG[slug.toLowerCase()] : undefined;
  return bySlug ?? Radar;
}

/* ----------------------------------------------------------------- difficulty */

export type DifficultyKey = 'easy' | 'medium' | 'hard' | 'expert';

export interface DifficultyMeta {
  label: string;
  /** Number of filled threat pips (1-4). */
  pips: number;
  text: string;
  bar: string;
  ring: string;
}

export const DIFFICULTY: Record<DifficultyKey, DifficultyMeta> = {
  easy: {
    label: 'LOW',
    pips: 1,
    text: 'text-accent',
    bar: 'bg-accent',
    ring: 'border-accent/40',
  },
  medium: {
    label: 'GUARDED',
    pips: 2,
    text: 'text-primary-glow',
    bar: 'bg-primary-glow',
    ring: 'border-primary/40',
  },
  hard: {
    label: 'ELEVATED',
    pips: 3,
    text: 'text-alert-soft',
    bar: 'bg-alert-soft',
    ring: 'border-alert/45',
  },
  expert: {
    label: 'SEVERE',
    pips: 4,
    text: 'text-alert',
    bar: 'bg-alert',
    ring: 'border-alert/60',
  },
};

export function difficultyMeta(value?: string | null): DifficultyMeta {
  const key = (value ?? 'easy').toLowerCase() as DifficultyKey;
  return DIFFICULTY[key] ?? DIFFICULTY.easy;
}
/* --------------------------------------------------------------- event intel */

export interface EventFallback {
  dateIso: string;
  dateLabel: string;
  venue: string;
  timezone: string;
  teamSize: number;
  submissionRatePerMinute: number;
  freezeMinutes: number;
}

/** Used only when the live competition row has no schedule set yet. */
export const EVENT_FALLBACK: EventFallback = {
  dateIso: import.meta.env.VITE_EVENT_DATE ?? '2026-03-14T09:00:00+05:30',
  dateLabel: 'SAT 14 MAR 2026',
  venue: import.meta.env.VITE_EVENT_VENUE ?? 'WANO Fest Main Campus — Cyber Lab Block',
  timezone: 'Asia/Kolkata',
  teamSize: 4,
  submissionRatePerMinute: 5,
  freezeMinutes: 15,
};

/* --------------------------------------------------------------------- rules */

export interface RuleGroup {
  id: string;
  title: string;
  summary: string;
  rules: { code: string; title: string; body: string }[];
}

export const RULE_GROUPS: RuleGroup[] = [
  {
    id: 'operation',
    title: 'OPERATION RULES',
    summary: 'How the engagement runs once the round goes live.',
    rules: [
      {
        code: 'R-01',
        title: 'One identity per operative',
        body: 'Every participant plays with a single registered account tied to their college and team. Sharing credentials, ghost-writing for another operative, or playing for two teams is disqualification.',
      },
      {
        code: 'R-02',
        title: 'Teams are locked at start',
        body: 'Team composition freezes when the round begins. Captains must finalise the roster before the opening brief — the platform refuses roster changes during a live operation.',
      },
      {
        code: 'R-03',
        title: 'Flags stay inside your team',
        body: 'Flags, hints, write-ups and solution paths are confidential until the round closes. Cross-team flag sharing forfeits every team involved, not only the recipient.',
      },
      {
        code: 'R-04',
        title: 'Target the challenges, never the platform',
        body: 'No denial-of-service, no flooding the submission endpoint, no attempting to reach the scoring database, admin console or another team’s session. Competition infrastructure is out of scope.',
      },
    ],
  },
  {
    id: 'scoring',
    title: 'SCORING PROTOCOL',
    summary: 'How points are awarded, deducted and tie-broken.',
    rules: [
      {
        code: 'S-01',
        title: 'Points scale with severity',
        body: 'Each challenge carries a fixed award weighted by difficulty. Submitted flags are matched against a peppered hash — the plaintext never leaves the database.',
      },
      {
        code: 'S-02',
        title: 'Hints cost points',
        body: 'Unlocking a hint deducts its stated cost from that challenge’s award. Penalties are visible on your dashboard before you commit to a reveal.',
      },
      {
        code: 'S-03',
        title: 'First blood is recorded',
        body: 'The first team to solve each challenge is flagged on the leaderboard and in the post-round results breakdown.',
      },
      {
        code: 'S-04',
        title: 'Tie-break on the clock',
        body: 'Equal scores are separated by the earliest final solve. Submissions are rate-limited per team — sustained flooding is throttled and logged.',
      },
    ],
  },
  {
    id: 'integrity',
    title: 'INTEGRITY & CONDUCT',
    summary: 'Professional standards enforced by the ops desk.',
    rules: [
      {
        code: 'I-01',
        title: 'Automate responsibly',
        body: 'Tooling, scripts and open-source research are encouraged. Blind brute-force against flags or endpoints is not — it is detected, throttled and reviewed.',
      },
      {
        code: 'I-02',
        title: 'No physical interference',
        body: 'Do not tamper with lab hardware, network infrastructure, power or seating. Report faulty equipment to the ops desk and it is replaced.',
      },
      {
        code: 'I-03',
        title: 'Report, do not exploit',
        body: 'If you discover an unintended flaw in the platform itself, report it to the ops desk immediately. Responsible disclosure earns recognition; exploitation triggers forensic review.',
      },
      {
        code: 'I-04',
        title: 'Zero tolerance',
        body: 'Harassment, discrimination, intimidation or sabotage results in immediate removal. The ops desk ruling is final, and disputes must be raised within 15 minutes of the affected event.',
      },
    ],
  },
];
/* ----------------------------------------------------------------- about copy */

export const MISSION_BRIEF = [
  'WANO CTF is the cyber operations division of WANO Fest — a national-level, offline capture-the-flag engagement built for students who want to prove they can operate under pressure.',
  'Round 1 drops your team inside a contested network. You will enumerate, exploit, decrypt, recover and defend across eight disciplines while a live scoreboard updates the instant a flag is verified.',
  'This is not a quiz. Every challenge is engineered to mirror a real incident-response or red-team scenario, and every point is earned against the clock.',
];

export const OPERATION_PHASES = [
  {
    phase: 'PHASE 01',
    title: 'Deployment & briefing',
    body: 'Check in at the ops desk, validate your roster, collect credentials and receive the rules of engagement for the round.',
  },
  {
    phase: 'PHASE 02',
    title: 'Operation goes live',
    body: 'All categories unlock simultaneously. The leaderboard opens and the operation clock starts running.',
  },
  {
    phase: 'PHASE 03',
    title: 'Escalation window',
    body: 'Hints release on demand. Scoreboard freeze engages fifteen minutes before close so final submissions land without inference.',
  },
  {
    phase: 'PHASE 04',
    title: 'Debrief & standings',
    body: 'Flags are frozen, the results breakdown is published and the leading teams are debriefed by the organisers.',
  },
];

export const FIELD_KIT = [
  'Laptop with a working network adapter (Wi-Fi or Ethernet)',
  'Your own tooling — Burp, Wireshark, Ghidra, CyberChef, scripting runtime',
  'Chargers, extension cords and any adapters you rely on',
  'Valid college identity card for every operative',
  'A team of up to four with a nominated captain',
];

/* ------------------------------------------------------------ terminal script */

export interface TerminalLine {
  command: string;
  output: string[];
}

/** Transcript replayed by the landing-page operations console. */
export const TERMINAL_SCRIPT: TerminalLine[] = [
  {
    command: './start_ctf --team STRAWH4T --round 1',
    output: ['[ok] session established · operator verified · console online'],
  },
  {
    command: 'scan --environment',
    output: [
      'scanning challenge environment...',
      '20 targets online · 8 domains mapped · 39 intel fragments indexed',
    ],
  },
  {
    command: 'nmap -sV --top-ports 1000 target.wano-fest.com',
    output: [
      'PORT     STATE SERVICE   VERSION',
      '80/tcp   open  http      nginx 1.27 (misconfigured)',
      '443/tcp  open  ssl/http  vault-endpoint',
      'vulnerability detected :: auth-bypass (medium)',
    ],
  },
  {
    command: 'exploit --payload reverse_shell --target 80/tcp',
    output: [
      'sending payload...',
      'connection received from target',
      'flag captured: FLAG{********}',
    ],
  },
  {
    command: 'submit --flag FLAG{********}',
    output: ['verifying hash...', 'flag accepted · +150 pts · first blood logged'],
  },
];

/* -------------------------------------------------------------------- helpers */

export function pad(value: number, length = 2): string {
  return String(Math.max(0, Math.floor(value))).padStart(length, '0');
}

export interface DurationParts {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalMs: number;
}

export function splitDuration(ms: number): DurationParts {
  const totalMs = Math.max(0, ms);
  const totalSeconds = Math.floor(totalMs / 1000);
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    totalMs,
  };
}

export function formatStamp(iso?: string | null, fallback = 'TBA'): string {
  if (!iso) return fallback;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return fallback;
  const day = pad(date.getDate());
  const month = date.toLocaleString('en-GB', { month: 'short' }).toUpperCase();
  return `${day} ${month} ${date.getFullYear()} · ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function relativeTime(iso?: string | null): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diff = Date.now() - then;
  if (diff < 45_000) return 'just now';
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat('en-IN').format(Math.round(value));
}


