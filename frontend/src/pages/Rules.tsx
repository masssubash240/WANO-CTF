import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  FileText,
  Lock,
  Flame,
  Clock,
  ArrowRight,
  Cpu,
  Swords,
  Scroll,
  Anchor,
} from 'lucide-react';
import { SectionShell, PanelHeader } from '../components/warzone/ui';

const ANCIENT_SCROLL_DIRECTIVES = [
  {
    id: 'crew',
    title: 'CREW & SQUAD COMPOSITION',
    summary: 'Directives regarding operative identity, captaincy, and team roster freezing.',
    rules: [
      {
        code: 'SEC-01',
        title: 'One Captain, One Crew',
        body: 'Every operative is bound to a single registered crew. Operating across multiple vessels, ghost-writing for rivals, or credential sharing incurs immediate fleet disqualification.',
      },
      {
        code: 'SEC-02',
        title: 'Roster Lock at Dawn',
        body: 'Crew rosters are locked upon voyage commencement. Captains must ensure all 4 operatives are verified before the opening bell. No roster modifications are accepted during live engagement.',
      },
    ],
  },
  {
    id: 'engagement',
    title: 'CHALLENGE RULES & BOUNDARIES',
    summary: 'Target boundaries, denial-of-service bans, and platform immunity.',
    rules: [
      {
        code: 'ENG-01',
        title: 'Immunity of Fleet Infrastructure',
        body: 'All attacks must target designated challenge targets only. Denial-of-service, flood attacks against the score database, or attempting to breach another crew’s session is forbidden and blocked.',
      },
      {
        code: 'ENG-02',
        title: 'Confidentiality of Ancient Flags',
        body: 'Flags, decryptions, and solution payloads are strictly confidential to your crew. Sharing flags with rival crews forfeits all parties involved.',
      },
    ],
  },
  {
    id: 'submission',
    title: 'FLAG SUBMISSION & ENCRYPTION',
    summary: 'Standard flag syntax, peppered hash validation, and brute-force throttling.',
    rules: [
      {
        code: 'SUB-01',
        title: 'Standard Flag Anatomy: WANO{...}',
        body: 'All accepted flags adhere to the standard format `WANO{...}` unless stated otherwise. Flags are hashed and validated in constant-time against salted cryptographic secrets.',
      },
      {
        code: 'SUB-02',
        title: 'Rate-Limited Transmissions',
        body: 'Flag transmissions are throttled to 5 requests per minute per crew. Blind brute-force attempts will trigger automated defense quarantines.',
      },
    ],
  },
  {
    id: 'scoring',
    title: 'SCORING & BOUNTY PROTOCOLS',
    summary: 'Dynamic points, first blood honours, and clue penalties.',
    rules: [
      {
        code: 'SCR-01',
        title: 'Bounties Scale with Threat Severity',
        body: 'Each conquered island awards bounty points according to its threat level (Low, Guarded, Elevated, Severe). First blood solvers receive permanent recognition on the Grand Line manifest.',
      },
      {
        code: 'SCR-02',
        title: 'Poneglyph Clue Penalties',
        body: 'Deciphering hints incurs the stated point penalty deducted directly from that challenge award upon solve.',
      },
      {
        code: 'SCR-03',
        title: 'Time-Resolved Tiebreak',
        body: 'Ties in points are resolved strictly by the earliest timestamp of the crew’s final accepted flag submission.',
      },
    ],
  },
  {
    id: 'anticheat',
    title: 'ANTI-CHEAT & BUSTER CALL',
    summary: 'Automated telemetry integrity, physical lab rules, and zero tolerance.',
    rules: [
      {
        code: 'ACT-01',
        title: 'Automated Anomaly Detection',
        body: 'The Ops Desk runs continuous behavioral anomaly detection. Flag sharing, concurrent multi-IP anomalies, or pre-computed leaks trigger an immediate Buster Call review.',
      },
      {
        code: 'ACT-02',
        title: 'Responsible Disclosure',
        body: 'If you discover an unintended vulnerability within platform infrastructure, report it to the Ops Desk immediately for bounty recognition rather than exploitation.',
      },
    ],
  },
  {
    id: 'event',
    title: 'VOYAGE TIMELINE & ARBITRATION',
    summary: 'Log pose freeze, dispute windows, and debriefing guidelines.',
    rules: [
      {
        code: 'EVT-01',
        title: 'Log Pose Freeze Window',
        body: 'Fifteen minutes prior to round conclusion, the public leaderboard is frozen. Final flag submissions are logged silently until the closing debrief.',
      },
      {
        code: 'EVT-02',
        title: 'Ops Desk Arbitration Ruling',
        body: 'The Chief Ops Desk holds sole authority over disputes. Official appeals must be lodged at the desk within 15 minutes of the final horn.',
      },
    ],
  },
];

const PIRATE_FIELD_KIT = [
  'Laptop workstation with working Wi-Fi & Ethernet network adapters',
  'Pre-installed security toolkit (Burp Suite, Wireshark, Ghidra, CyberChef, Python runtime)',
  'Power cords, multi-pin extension strips, and display adapters',
  'Valid college identification card for each crew member',
  'A registered crew of up to four operatives with an elected Captain',
];

export const Rules: React.FC = () => {
  const [activeSection, setActiveSection] = useState('crew');
  const [checkedKit, setCheckedKit] = useState<Record<number, boolean>>({});

  const toggleKit = (index: number) => {
    setCheckedKit((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const selectedDirective = ANCIENT_SCROLL_DIRECTIVES.find((d) => d.id === activeSection) || ANCIENT_SCROLL_DIRECTIVES[0];

  return (
    <div className="relative pb-24 pt-6">
      {/* Background subtle radial gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(224,47,62,0.1),_transparent_60%)] -z-10" />

      <SectionShell
        kicker="RULES OF ENGAGEMENT"
        title="ANCIENT DIRECTIVES & PROTOCOLS"
        description="Every pirate crew operating in WANO CTF is bound by the Grand Line Directives. Enforcement is continuous and governed by the Chief Ops Desk."
      >
        {/* Core summary cards */}
        <div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="p-5 rounded-2xl border border-gold/40 bg-surface/80 shadow-glow-gold">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl border border-gold/30 bg-gold/10 text-gold">
                <Anchor className="h-5 w-5" />
              </div>
              <div>
                <div className="label-hud text-gold">CREW INTEGRITY</div>
                <div className="font-display font-bold text-white text-sm">ISOLATED CREWS</div>
              </div>
            </div>
            <p className="mt-3 text-xs text-steel-400">Zero flag sharing across rival crews. One crew per operative.</p>
          </div>

          <div className="p-5 rounded-2xl border border-crimson/40 bg-surface/80 shadow-glow-crimson">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl border border-crimson/30 bg-crimson/10 text-crimson-glow">
                <Lock className="h-5 w-5" />
              </div>
              <div>
                <div className="label-hud text-crimson">TARGET BOUNDARY</div>
                <div className="font-display font-bold text-white text-sm">NO PLATFORM ATTACKS</div>
              </div>
            </div>
            <p className="mt-3 text-xs text-steel-400">Target challenges only. Platform DDoS triggers immediate Buster Call.</p>
          </div>

          <div className="p-5 rounded-2xl border border-accent/40 bg-surface/80">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl border border-accent/30 bg-accent/10 text-accent">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <div className="label-hud text-accent">SCORING</div>
                <div className="font-display font-bold text-white text-sm">DYNAMIC BOUNTIES</div>
              </div>
            </div>
            <p className="mt-3 text-xs text-steel-400">Points scale with threat severity. Clues deduct point penalties.</p>
          </div>

          <div className="p-5 rounded-2xl border border-amber-500/40 bg-surface/80">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-400">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <div className="label-hud text-amber-400">LOG POSE FREEZE</div>
                <div className="font-display font-bold text-white text-sm">15-MIN ESCALATION</div>
              </div>
            </div>
            <p className="mt-3 text-xs text-steel-400">Rankings freeze 15 mins before close for thrilling finish.</p>
          </div>
        </div>

        {/* Ancient Scroll + Cyber UI Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Scroll Navigation */}
          <div className="lg:col-span-4 space-y-3">
            <div className="label-hud text-gold mb-2 flex items-center gap-2">
              <Scroll className="h-4 w-4 text-gold" />
              <span>DIRECTIVE SCROLLS</span>
            </div>

            {ANCIENT_SCROLL_DIRECTIVES.map((directive) => {
              const isActive = activeSection === directive.id;
              return (
                <button
                  key={directive.id}
                  onClick={() => setActiveSection(directive.id)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all duration-300 ${
                    isActive
                      ? 'border-gold bg-gradient-to-r from-gold/20 to-crimson/15 shadow-glow-gold text-white'
                      : 'border-card-border/80 bg-surface/60 hover:bg-surface/90 hover:border-gold/40 text-steel-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-display font-bold text-sm tracking-wide">{directive.title}</span>
                    <span className="label-hud text-gold font-mono">[{directive.rules.length} RULES]</span>
                  </div>
                  <p className="mt-1 text-xs text-steel-400 line-clamp-2">{directive.summary}</p>
                </button>
              );
            })}

            {/* Field Kit Checklist */}
            <div className="mt-8 rounded-2xl border border-gold/30 bg-void/80 p-5 shadow-hud">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="h-4 w-4 text-gold" />
                <span className="font-display font-bold text-sm text-white uppercase">PIRATE FIELD KIT CHECKLIST</span>
              </div>
              <p className="text-xs text-steel-400 mb-4">Ensure your workstation is properly equipped before departing:</p>
              <div className="space-y-2.5">
                {PIRATE_FIELD_KIT.map((item, idx) => {
                  const isChecked = Boolean(checkedKit[idx]);
                  return (
                    <div
                      key={idx}
                      onClick={() => toggleKit(idx)}
                      className={`flex items-start gap-2.5 p-2 rounded-xl cursor-pointer transition-colors text-xs ${
                        isChecked ? 'bg-gold/15 text-white' : 'hover:bg-slate-800/40 text-steel-400'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-0.5 accent-amber-400 rounded cursor-pointer"
                      />
                      <span className={isChecked ? 'line-through text-steel-400' : ''}>{item}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Detailed Directive Content */}
          <div className="lg:col-span-8">
            <div className="wano-scroll-frame">
              <PanelHeader
                kicker={selectedDirective.id.toUpperCase()}
                title={selectedDirective.title}
                right={
                  <span className="chip text-gold border-gold/40 bg-gold/10 font-bold">
                    STATUS: ACTIVE
                  </span>
                }
              />
              <p className="mt-2 text-sm text-steel-300">{selectedDirective.summary}</p>

              <div className="hair-line-gold my-6" />

              <div className="space-y-6">
                {selectedDirective.rules.map((rule) => (
                  <div
                    key={rule.code}
                    className="p-5 rounded-2xl border border-card-border/90 bg-void/70 hover:border-gold/50 transition-all duration-300"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-xs font-bold text-gold px-2.5 py-0.5 rounded-full bg-gold/10 border border-gold/30">
                        {rule.code}
                      </span>
                      <h4 className="font-display font-bold text-white text-base">{rule.title}</h4>
                    </div>
                    <p className="text-sm text-steel-300 leading-relaxed pl-1">{rule.body}</p>
                  </div>
                ))}
              </div>

              {/* Dispute Resolution Arbitration */}
              <div className="mt-8 p-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex items-start gap-3 text-xs text-amber-200/90">
                <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-amber-400 font-mono">BUSTER CALL ARBITRATION:</span> In the event of network disruption or disputes, the Chief Ops Desk ruling is final and binding. Appeals must be lodged in person within 15 minutes of round conclusion.
                </div>
              </div>

              <div className="mt-8 flex items-center justify-between">
                <Link
                  to="/challenges"
                  className="hud-btn-gold inline-flex items-center gap-2 text-xs"
                >
                  <Swords className="h-4 w-4" />
                  <span>COMMENCE EXPEDITION</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="hud-btn-ghost inline-flex items-center gap-2 text-xs"
                >
                  <FileText className="h-4 w-4" />
                  <span>MISSION INTEL</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </SectionShell>
    </div>
  );
};
