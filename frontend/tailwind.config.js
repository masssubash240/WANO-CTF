/**
 * WANO CTF — "PIRATE ADVENTURE × CYBER WARZONE / GRAND LINE OPERATIONS" design tokens.
 *
 * One palette, one type stack, one motion language for the entire site.
 * Blending dark oceanic depths, crimson blood moon, treasure gold, and cyber HUD optics.
 *
 * @type {import('tailwindcss').Config}
 */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        /* ---- environment ---------------------------------------------------- */
        void: '#05070A',
        background: '#05070A',
        surface: '#0B1118',
        card: '#0B1118',
        raised: '#111A24',
        'card-border': '#1B2A3A',
        line: '#1B2A3A',

        /* ---- signature pirate & cyber lighting ------------------------------ */
        primary: { DEFAULT: '#2B7FFF', glow: '#5EA8FF', dark: '#0F3C7A' },
        accent: { DEFAULT: '#3CDCF0', soft: '#93E9F4', dim: '#0E4C57' },
        alert: { DEFAULT: '#E0484E', soft: '#F08A8F', dim: '#4A1418' },

        /* ---- one piece × wano color tier ----------------------------------- */
        crimson: { DEFAULT: '#E02F3E', glow: '#FF4D5E', dark: '#7A1019', dim: '#3A080C' },
        gold: { DEFAULT: '#E5A93C', glow: '#FFE072', light: '#FFD166', dark: '#8F6312', dim: '#3E2A05' },
        ocean: { DEFAULT: '#1A538C', light: '#3A88D8', deep: '#091626', surface: '#0D2138' },

        /* ---- cool neutral text scale (AA contrast on the void black) --------- */
        steel: {
          100: '#E8EEF5',
          200: '#CBD8E4',
          300: '#A7B7C7',
          400: '#8397AB',
          500: '#647789',
          600: '#485A6B',
          700: '#33424F',
          800: '#212D38',
          900: '#141C25',
        },
        cyber: {
          green: '#2FD3A4',
          red: '#E0484E',
          yellow: '#E0A33C',
          purple: '#8B7FE8',
        },
      },
      fontFamily: {
        display: ['Orbitron', 'Rajdhani', 'Inter', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      },
      letterSpacing: {
        hud: '0.28em',
        ops: '0.16em',
      },
      boxShadow: {
        hud: '0 0 0 1px rgba(43,127,255,0.16), 0 24px 60px -28px rgba(0,0,0,0.95)',
        'hud-hover': '0 0 0 1px rgba(60,220,240,0.32), 0 30px 70px -26px rgba(0,0,0,0.95)',
        'glow-blue': '0 0 24px -4px rgba(43,127,255,0.55)',
        'glow-cyan': '0 0 26px -4px rgba(60,220,240,0.5)',
        'glow-alert': '0 0 22px -6px rgba(224,72,78,0.55)',
        'glow-crimson': '0 0 30px -4px rgba(224,47,62,0.65)',
        'glow-gold': '0 0 30px -4px rgba(229,169,60,0.65)',
        wanted: '0 0 0 1px rgba(229,169,60,0.3), 0 20px 50px -15px rgba(0,0,0,0.9)',
        inset: 'inset 0 1px 0 0 rgba(255,255,255,0.05)',
      },
      backgroundImage: {
        'hud-grid':
          'linear-gradient(rgba(43,127,255,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(43,127,255,0.07) 1px, transparent 1px)',
        'hud-fade': 'radial-gradient(ellipse at 50% 0%, rgba(43,127,255,0.14), transparent 62%)',
        'blood-moon': 'radial-gradient(circle at 50% 20%, rgba(224,47,62,0.25), rgba(5,7,10,0.95) 70%)',
        'treasure-grid':
          'linear-gradient(rgba(229,169,60,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(229,169,60,0.08) 1px, transparent 1px)',
        'panel-sheen':
          'linear-gradient(135deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.012) 34%, transparent 60%)',
        'optic-scan': 'linear-gradient(180deg, transparent, rgba(60,220,240,0.55), transparent)',
      },
      backgroundSize: {
        'grid-md': '46px 46px',
        'grid-sm': '22px 22px',
      },
      keyframes: {
        drift: {
          '0%,100%': { transform: 'translate3d(0,0,0) scale(1)' },
          '50%': { transform: 'translate3d(2%,-3%,0) scale(1.06)' },
        },
        sweep: {
          '0%': { transform: 'translateY(-110%)', opacity: '0' },
          '12%': { opacity: '0.85' },
          '88%': { opacity: '0.85' },
          '100%': { transform: 'translateY(920%)', opacity: '0' },
        },
        stream: {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(-50%)' },
        },
        floaty: {
          '0%,100%': { transform: 'translateY(-6px)' },
          '50%': { transform: 'translateY(6px)' },
        },
        'wave-drift': {
          '0%': { transform: 'translateX(0)' },
          '50%': { transform: 'translateX(-25px)' },
          '100%': { transform: 'translateX(0)' },
        },
        blink: {
          '0%,42%': { opacity: '1' },
          '50%,92%': { opacity: '0.18' },
          '100%': { opacity: '1' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.85)', opacity: '0.6' },
          '70%': { transform: 'scale(1.5)', opacity: '0' },
          '100%': { transform: 'scale(1.5)', opacity: '0' },
        },
        'shell-flicker': {
          '0%,100%': { opacity: '0.04' },
          '48%': { opacity: '0.05' },
          '50%': { opacity: '0.085' },
          '52%': { opacity: '0.045' },
        },
      },
      animation: {
        drift: 'drift 26s ease-in-out infinite',
        'drift-slow': 'drift 44s ease-in-out infinite',
        sweep: 'sweep 7.5s cubic-bezier(0.4,0,0.2,1) infinite',
        stream: 'stream 9s linear infinite',
        floaty: 'floaty 6s ease-in-out infinite',
        'wave-drift': 'wave-drift 12s ease-in-out infinite',
        blink: 'blink 3.4s steps(1,end) infinite',
        'pulse-ring': 'pulse-ring 3.2s ease-out infinite',
        'shell-flicker': 'shell-flicker 8s ease-in-out infinite',
      },
      transitionTimingFunction: {
        cinema: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      screens: {
        xs: '420px',
      },
    },
  },
  plugins: [],
};
