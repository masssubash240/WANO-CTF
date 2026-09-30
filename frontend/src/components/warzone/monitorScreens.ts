/**
 * Procedural monitor surfaces for the hero command centre.
 *
 * Each factory paints a 2D canvas and hands back a THREE.CanvasTexture plus a
 * `draw(t)` updater, so the 3D workstation renders live terminals, traffic
 * graphs and vulnerability scans without shipping video or large images.
 */
import * as THREE from 'three';

export interface ScreenSurface {
  texture: THREE.CanvasTexture;
  /** Redraw for wall-clock `time` (seconds). Called at a low frame rate. */
  draw: (time: number) => void;
}

const SCREEN_W = 640;
const SCREEN_H = 400;

const PALETTE = {
  void: '#04070B',
  grid: 'rgba(43,127,255,0.16)',
  dim: '#5D7488',
  text: '#A7B7C7',
  bright: '#E8EEF5',
  blue: '#2B7FFF',
  cyan: '#3CDCF0',
  green: '#2FD3A4',
  red: '#E0484E',
  amber: '#E0A33C',
};

function createCanvas(): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = SCREEN_W;
  canvas.height = SCREEN_H;
  return canvas;
}

function toTexture(canvas: HTMLCanvasElement): THREE.CanvasTexture {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  texture.anisotropy = 2;
  return texture;
}

/** Common window chrome: title bar, traffic lights, accent rule. */
function shell(ctx: CanvasRenderingContext2D, title: string, accent: string = PALETTE.cyan): void {
  ctx.fillStyle = PALETTE.void;
  ctx.fillRect(0, 0, SCREEN_W, SCREEN_H);

  const bar = ctx.createLinearGradient(0, 0, SCREEN_W, 0);
  bar.addColorStop(0, '#0A1520');
  bar.addColorStop(1, '#08111A');
  ctx.fillStyle = bar;
  ctx.fillRect(0, 0, SCREEN_W, 30);
  ctx.fillStyle = accent;
  ctx.fillRect(0, 29, SCREEN_W, 1);

  [PALETTE.red, PALETTE.amber, PALETTE.green].forEach((colour, index) => {
    ctx.beginPath();
    ctx.arc(18 + index * 16, 15, 4.4, 0, Math.PI * 2);
    ctx.fillStyle = colour;
    ctx.fill();
  });

  ctx.font = '600 13px "JetBrains Mono", monospace';
  ctx.fillStyle = PALETTE.dim;
  ctx.textAlign = 'center';
  ctx.fillText(title, SCREEN_W / 2, 20);
  ctx.textAlign = 'left';
}

/** Faint blueprint grid behind every feed. */
function grid(ctx: CanvasRenderingContext2D, step = 32): void {
  ctx.strokeStyle = PALETTE.grid;
  ctx.lineWidth = 1;
  for (let x = 0; x <= SCREEN_W; x += step) {
    ctx.beginPath();
    ctx.moveTo(x + 0.5, 30);
    ctx.lineTo(x + 0.5, SCREEN_H);
    ctx.stroke();
  }
  for (let y = 30; y <= SCREEN_H; y += step) {
    ctx.beginPath();
    ctx.moveTo(0, y + 0.5);
    ctx.lineTo(SCREEN_W, y + 0.5);
    ctx.stroke();
  }
}
/* --------------------------------------------------------- monitor 01 · shell */

interface ScriptLine {
  text: string;
  kind: 'cmd' | 'out' | 'ok' | 'warn' | 'flag';
}

interface TimedLine extends ScriptLine {
  start: number;
  end: number;
}

const MONITOR_SCRIPT: ScriptLine[] = [
  { text: './start_ctf --team STRAWH4T --round 1', kind: 'cmd' },
  { text: '[ok] session established · operator verified', kind: 'ok' },
  { text: 'scanning challenge environment...', kind: 'out' },
  { text: '20 targets online · 8 domains mapped', kind: 'out' },
  { text: 'nmap -sV --top-ports 1000 10.10.4.11', kind: 'cmd' },
  { text: '80/tcp   open  http      nginx 1.27', kind: 'out' },
  { text: '443/tcp  open  ssl/http  vault-endpoint', kind: 'out' },
  { text: 'vulnerability detected :: auth-bypass', kind: 'warn' },
  { text: 'flag captured: FLAG{********}', kind: 'flag' },
  { text: 'submit --flag FLAG{********}', kind: 'cmd' },
  { text: 'flag accepted · +150 pts · first blood', kind: 'ok' },
];

const CHAR_RATE = 46; // characters per second while a command types out

/** Deterministic typing timeline so `draw(t)` stays stateless. */
function buildTimeline(script: ScriptLine[]): { lines: TimedLine[]; total: number } {
  let cursor = 0.35;
  const lines = script.map((line) => {
    const start = cursor;
    const typed = line.kind === 'cmd' ? line.text.length / CHAR_RATE : 0.06;
    const end = start + Math.max(0.12, typed);
    cursor = end + (line.kind === 'cmd' ? 0.28 : 0.16);
    return { ...line, start, end };
  });
  return { lines, total: cursor + 3.4 };
}

export function createTerminalScreen(): ScreenSurface {
  const canvas = createCanvas();
  const ctx = canvas.getContext('2d');
  const texture = toTexture(canvas);
  const { lines, total } = buildTimeline(MONITOR_SCRIPT);
  const colours: Record<ScriptLine['kind'], string> = {
    cmd: PALETTE.bright,
    out: PALETTE.text,
    ok: PALETTE.green,
    warn: PALETTE.amber,
    flag: PALETTE.cyan,
  };

  const draw = (time: number): void => {
    if (!ctx) return;
    const local = time % total;
    shell(ctx, 'root@wano-ops: ~/ctf');
    grid(ctx);

    ctx.font = '500 14px "JetBrains Mono", monospace';
    let y = 58;
    lines.forEach((line) => {
      if (local < line.start) return;
      const span = Math.max(0.01, line.end - line.start);
      const progress = Math.min(1, (local - line.start) / span);
      const visible =
        line.kind === 'cmd' ? line.text.slice(0, Math.ceil(line.text.length * progress)) : line.text;

      ctx.fillStyle = line.kind === 'cmd' ? PALETTE.cyan : 'rgba(60,220,240,0.35)';
      ctx.fillText(line.kind === 'cmd' ? '$' : '>', 16, y);

      ctx.fillStyle = colours[line.kind];
      ctx.fillText(visible, 34, y);

      if (line.kind === 'cmd' && progress < 1) {
        ctx.fillStyle = PALETTE.cyan;
        ctx.fillRect(34 + ctx.measureText(visible).width + 2, y - 11, 8, 13);
      }
      y += 26;
    });

    if (Math.floor(time * 2) % 2 === 0) {
      ctx.fillStyle = PALETTE.cyan;
      ctx.fillRect(16, y - 11, 9, 14);
    }

    ctx.fillStyle = 'rgba(43,127,255,0.5)';
    ctx.fillRect(0, SCREEN_H - 22, SCREEN_W, 1);
    ctx.font = '500 11px "JetBrains Mono", monospace';
    ctx.fillStyle = PALETTE.dim;
    ctx.fillText(`uptime ${Math.floor(time)}s`, 14, SCREEN_H - 7);
    ctx.fillText('rate 5/min', SCREEN_W - 190, SCREEN_H - 7);
    ctx.fillStyle = PALETTE.green;
    ctx.fillText('● linked', SCREEN_W - 74, SCREEN_H - 7);

    texture.needsUpdate = true;
  };

  draw(0);
  return { texture, draw };
}
/* ------------------------------------------------------ monitor 02 · traffic */

const PEERS = [
  { addr: '10.10.4.11:80', label: 'nginx', ok: true },
  { addr: '10.10.4.12:443', label: 'vault', ok: true },
  { addr: '10.10.4.31:22', label: 'sshd', ok: true },
  { addr: '10.10.4.44:5432', label: 'pg', ok: false },
  { addr: '10.10.4.9:8443', label: 'api', ok: true },
];

const PROTOCOLS = [
  { name: 'TCP', colour: PALETTE.cyan, weight: 0.72 },
  { name: 'UDP', colour: PALETTE.blue, weight: 0.42 },
  { name: 'TLS', colour: PALETTE.green, weight: 0.58 },
  { name: 'ICMP', colour: PALETTE.amber, weight: 0.2 },
];

export function createTrafficScreen(): ScreenSurface {
  const canvas = createCanvas();
  const ctx = canvas.getContext('2d');
  const texture = toTexture(canvas);
  const samples = 72;

  const draw = (time: number): void => {
    if (!ctx) return;
    shell(ctx, 'netflow · eth0 · promiscuous', PALETTE.blue);
    grid(ctx);

    const index0 = Math.floor(time * 14);

    // --- packet volume chart ------------------------------------------------
    const left = 26;
    const right = SCREEN_W - 26;
    const top = 52;
    const bottom = 206;
    const width = right - left;
    const step = width / (samples - 1);

    ctx.strokeStyle = 'rgba(60,220,240,0.45)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    for (let i = 0; i < samples; i += 1) {
      const seed = index0 + i;
      const burst = seed % 41 === 0 ? 0.42 : 0;
      const value =
        0.34 +
        0.16 * Math.sin(seed * 0.21) +
        0.1 * Math.sin(seed * 0.07 + 1.3) +
        burst +
        (seed % 97 === 0 ? 0.26 : 0);
      const x = left + i * step;
      const y = bottom - Math.min(1, Math.max(0.04, value)) * (bottom - top);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Filled area under the curve.
    ctx.lineTo(right, bottom);
    ctx.lineTo(left, bottom);
    ctx.closePath();
    const fill = ctx.createLinearGradient(0, top, 0, bottom);
    fill.addColorStop(0, 'rgba(60,220,240,0.26)');
    fill.addColorStop(1, 'rgba(43,127,255,0.02)');
    ctx.fillStyle = fill;
    ctx.fill();

    // --- axis labels -------------------------------------------------------
    ctx.font = '500 11px "JetBrains Mono", monospace';
    ctx.fillStyle = PALETTE.dim;
    ctx.fillText('pps 1.2M', left, top - 8);
    ctx.fillText('window 60s', right - 96, top - 8);

    // --- protocol bars -----------------------------------------------------
    const barTop = 236;
    const barBottom = 306;
    ctx.fillText('protocol mix', left, barTop - 10);
    PROTOCOLS.forEach((proto, index) => {
      const x = left + index * 104;
      const pulsate = 0.82 + 0.18 * Math.sin(time * 0.9 + index);
      const height = (barBottom - barTop) * proto.weight * pulsate;
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(x, barTop, 74, barBottom - barTop);
      ctx.fillStyle = proto.colour;
      ctx.fillRect(x, barBottom - height, 74, height);
      ctx.fillStyle = PALETTE.dim;
      ctx.fillText(proto.name, x, barBottom + 16);
    });

    // --- peer table --------------------------------------------------------
    const tableX = SCREEN_W - 250;
    ctx.fillStyle = PALETTE.dim;
    ctx.fillText('peers', tableX, 336);
    PEERS.forEach((peer, index) => {
      const y = 352 + index * 10;
      if (y > SCREEN_H - 6) return;
      ctx.fillStyle = peer.ok ? PALETTE.green : PALETTE.red;
      ctx.beginPath();
      ctx.arc(tableX + 4, y - 4, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = PALETTE.text;
      ctx.fillText(peer.addr, tableX + 14, y);
      ctx.fillStyle = PALETTE.dim;
      ctx.fillText(peer.label, tableX + 152, y);
    });

    // --- raw hex ticker ----------------------------------------------------
    ctx.fillStyle = 'rgba(60,220,240,0.5)';
    ctx.font = '500 11px "JetBrains Mono", monospace';
    for (let row = 0; row < 6; row += 1) {
      let line = '';
      for (let column = 0; column < 6; column += 1) {
        const value = Math.floor(Math.abs(Math.sin((index0 + row * 7 + column * 13) * 0.37)) * 65535);
        line += `${value.toString(16).toUpperCase().padStart(4, '0')} `;
      }
      ctx.fillText(line, left, 336 + row * 10);
    }

    texture.needsUpdate = true;
  };

  draw(0);
  return { texture, draw };
}
/* --------------------------------------------------------- monitor 03 · scan */

const FINDINGS = [
  { sev: 'CRIT', name: 'auth-bypass :: /admin', host: '10.10.4.11', colour: PALETTE.red },
  { sev: 'HIGH', name: 'sql-injection :: /search', host: '10.10.4.11', colour: PALETTE.red },
  { sev: 'HIGH', name: 'weak-jwt-secret', host: '10.10.4.9', colour: PALETTE.amber },
  { sev: 'MED', name: 'directory-listing', host: '10.10.4.12', colour: PALETTE.amber },
  { sev: 'MED', name: 'tls-1.0 accepted', host: '10.10.4.12', colour: PALETTE.amber },
  { sev: 'LOW', name: 'server banner leak', host: '10.10.4.31', colour: PALETTE.cyan },
];

const TOPOLOGY: { x: number; y: number }[] = [
  { x: 0.5, y: 0.12 },
  { x: 0.16, y: 0.36 },
  { x: 0.84, y: 0.36 },
  { x: 0.3, y: 0.66 },
  { x: 0.7, y: 0.66 },
  { x: 0.5, y: 0.92 },
];

export function createScanScreen(): ScreenSurface {
  const canvas = createCanvas();
  const ctx = canvas.getContext('2d');
  const texture = toTexture(canvas);

  const draw = (time: number): void => {
    if (!ctx) return;
    shell(ctx, 'vuln-scan --deep · 10.10.4.0/24', PALETTE.amber);

    const progress = (time % 9) / 9;

    // --- sweep bar ---------------------------------------------------------
    ctx.fillStyle = 'rgba(43,127,255,0.16)';
    ctx.fillRect(24, 46, 420, 7);
    ctx.fillStyle = PALETTE.cyan;
    ctx.fillRect(24, 46, 420 * progress, 7);
    ctx.font = '500 11px "JetBrains Mono", monospace';
    ctx.fillStyle = PALETTE.dim;
    ctx.fillText(`scanning subnet · ${Math.round(progress * 100)}%`, 24, 70);
    ctx.fillText('cve-db 2026.09', 320, 70);

    // --- findings ----------------------------------------------------------
    ctx.font = '600 12px "JetBrains Mono", monospace';
    ctx.fillStyle = PALETTE.bright;
    ctx.fillText('findings', 24, 96);

    FINDINGS.forEach((finding, index) => {
      const revealed = time * 0.55 > index + 0.4;
      const y = 122 + index * 32;
      ctx.globalAlpha = revealed ? 1 : 0.12;

      ctx.fillStyle = 'rgba(255,255,255,0.045)';
      ctx.fillRect(24, y - 15, 420, 24);
      ctx.fillStyle = finding.colour;
      ctx.fillRect(24, y - 15, 3, 24);

      ctx.font = '700 10px "JetBrains Mono", monospace';
      ctx.fillStyle = finding.colour;
      ctx.fillText(finding.sev, 36, y + 2);

      ctx.font = '500 12px "JetBrains Mono", monospace';
      ctx.fillStyle = PALETTE.text;
      ctx.fillText(finding.name, 82, y + 2);

      ctx.fillStyle = PALETTE.dim;
      ctx.fillText(finding.host, 372, y + 2);
      ctx.globalAlpha = 1;
    });

    // --- topology hologram -------------------------------------------------
    const boxX = 462;
    const boxY = 42;
    const boxW = 152;
    const boxH = 210;
    ctx.strokeStyle = 'rgba(43,127,255,0.35)';
    ctx.strokeRect(boxX + 0.5, boxY + 0.5, boxW, boxH);
    ctx.fillStyle = 'rgba(43,127,255,0.05)';
    ctx.fillRect(boxX, boxY, boxW, boxH);

    ctx.font = '600 10px "JetBrains Mono", monospace';
    ctx.fillStyle = PALETTE.dim;
    ctx.fillText('topology', boxX + 10, boxY + 16);

    const nodes = TOPOLOGY.map((node) => ({
      x: boxX + 16 + node.x * (boxW - 32),
      y: boxY + 30 + node.y * (boxH - 48),
    }));

    ctx.strokeStyle = 'rgba(60,220,240,0.45)';
    ctx.lineWidth = 1;
    nodes.forEach((node, index) => {
      const target = nodes[(index + 1) % nodes.length];
      ctx.beginPath();
      ctx.moveTo(node.x, node.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();
    });
    ctx.beginPath();
    ctx.moveTo(nodes[0].x, nodes[0].y);
    ctx.lineTo(nodes[3].x, nodes[3].y);
    ctx.moveTo(nodes[0].x, nodes[0].y);
    ctx.lineTo(nodes[4].x, nodes[4].y);
    ctx.stroke();

    nodes.forEach((node, index) => {
      const pulse = 0.5 + 0.5 * Math.sin(time * 2 + index);
      ctx.beginPath();
      ctx.arc(node.x, node.y, 4 + pulse * 2.4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(60,220,240,${0.18 + pulse * 0.3})`;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(node.x, node.y, 2.6, 0, Math.PI * 2);
      ctx.fillStyle = PALETTE.cyan;
      ctx.fill();
    });

    // --- binary rain -------------------------------------------------------
    ctx.font = '500 12px "JetBrains Mono", monospace';
    for (let column = 0; column < 2; column += 1) {
      const x = boxX + 18 + column * 70;
      for (let row = 0; row < 9; row += 1) {
        const offset = Math.floor(time * 6) + row;
        const bits = Array.from(
          { length: 6 },
          (_, bit) => (Math.abs(Math.sin((offset + bit * 3 + column * 11) * 1.7)) > 0.5 ? '1' : '0')
        ).join('');
        ctx.fillStyle = `rgba(60,220,240,${Math.max(0.12, (1 - row / 12) * 0.75)})`;
        ctx.fillText(bits, x, boxY + 34 + row * 18);
      }
    }

    texture.needsUpdate = true;
  };

  draw(0);
  return { texture, draw };
}
/* ------------------------------------------- background wall · glyph downpour */

const GLYPHS = '01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ#$%&@+=<>{}[]/\\';

/** Tileable falling-glyph wall; the scene scrolls `texture.offset.y`. */
export function createRainTexture(): THREE.CanvasTexture {
  const size = 512;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  if (ctx) {
    ctx.fillStyle = 'rgba(3,6,10,1)';
    ctx.fillRect(0, 0, size, size);
    ctx.font = '600 14px "JetBrains Mono", monospace';

    const columns = 26;
    const stepX = size / columns;
    for (let column = 0; column < columns; column += 1) {
      const phase = (column * 37) % 23;
      for (let row = 0; row < 40; row += 1) {
        const bright = (row - phase + 40) % 40;
        if (bright > 22) continue;
        const intensity = Math.max(0.05, 1 - bright / 22);
        const glyph = GLYPHS[(column * 7 + row * 13) % GLYPHS.length];
        ctx.fillStyle =
          bright === 0
            ? `rgba(214,247,255,${0.85 * intensity + 0.2})`
            : `rgba(60,220,240,${0.5 * intensity})`;
        ctx.fillText(glyph, column * stepX + 4, row * 13);
      }
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}




