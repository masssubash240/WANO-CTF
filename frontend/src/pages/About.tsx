import React from 'react';
import { Link } from 'react-router-dom';
import {
  MapPin,
  Calendar,
  Users,
  Clock,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
import {
  SOCIAL_LINKS,
  EVENT_FALLBACK,
} from '../lib/warzone';
import { SectionShell, PanelHeader, Reveal } from '../components/warzone/ui';

const GRAND_LINE_NARRATIVE = [
  'WANO CTF is the flagship collegiate cybersecurity expedition of WANO Fest — a national-level, offline capture-the-flag voyage engineered for operatives who dare to conquer the New World.',
  'Your squad of four enters a contested cyber archipelago. You will enumerate, breach, decipher, recover, and defend across eight high-security island domains while a real-time bounty manifest reflects every accepted solve.',
  'This is not a quiz. Every target is engineered from real incident-response and offensive red-team engagements. Every bounty is earned under the pressure of the clock.',
];

const VOYAGE_PHASES = [
  {
    phase: 'VOYAGE 01',
    title: 'Fleet Deployment & Briefing',
    body: 'Check in at the Chief Ops Desk, verify your crew roster, collect credentials, and receive the Grand Line Directives.',
  },
  {
    phase: 'VOYAGE 02',
    title: 'The Grand Line Goes Live',
    body: 'All eight island sectors unlock simultaneously. The bounty manifest opens and the expedition clock starts running.',
  },
  {
    phase: 'VOYAGE 03',
    title: 'Escalation & Log Pose Freeze',
    body: 'Poneglyph clues unlock on demand. Log pose freeze engages 15 minutes before close so final captures land in secrecy.',
  },
  {
    phase: 'VOYAGE 04',
    title: 'Debrief & Crowning of Pirate King',
    body: 'Target ports freeze, final rankings are unveiled, and top crews are awarded their official bounties and trophies.',
  },
];

export const About: React.FC = () => {
  return (
    <div className="relative pb-24 pt-6">
      {/* Background subtle radial gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(229,169,60,0.1),_transparent_60%)] -z-10" />

      <SectionShell
        kicker="MISSION INTEL"
        title="ABOUT WANO CTF"
        description="The premier college-level offline cyber competition platform inspired by the Grand Line expedition and engineered for high-stakes cybersecurity combat."
      >
        {/* Mission Briefing Card */}
        <Reveal>
          <div className="wano-scroll-frame mb-12">
            <PanelHeader
              kicker="EXECUTIVE SUMMARY"
              title="THE GRAND LINE ENGAGEMENT ARCHITECTURE"
              right={
                <span className="chip text-gold border-gold/40 bg-gold/10 font-bold">
                  CLEARANCE: PUBLIC
                </span>
              }
            />
            <div className="hair-line-gold my-6" />

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
              <div className="lg:col-span-8 space-y-4 text-steel-200 leading-relaxed text-sm sm:text-base font-sans">
                {GRAND_LINE_NARRATIVE.map((paragraph, idx) => (
                  <p key={idx}>{paragraph}</p>
                ))}
              </div>

              <div className="lg:col-span-4 rounded-2xl border border-gold/30 bg-void/80 p-6 space-y-4 shadow-hud">
                <div className="label-hud text-gold">EXPEDITION AT A GLANCE</div>
                <div className="space-y-3 font-mono text-xs text-steel-300">
                  <div className="flex items-center gap-2.5">
                    <Calendar className="h-4 w-4 text-gold" />
                    <span>{EVENT_FALLBACK.dateLabel}</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <MapPin className="h-4 w-4 text-crimson" />
                    <span>{EVENT_FALLBACK.venue}</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Users className="h-4 w-4 text-accent" />
                    <span>Max {EVENT_FALLBACK.teamSize} Operatives per Crew</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Clock className="h-4 w-4 text-amber-400" />
                    <span>Log Pose Freeze: {EVENT_FALLBACK.freezeMinutes} mins before close</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link
                    to="/register"
                    className="hud-btn-gold w-full inline-flex items-center justify-center gap-2 text-xs font-bold"
                  >
                    <span>ENROLL SQUAD</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </Reveal>

        {/* 4-Phase Roadmap */}
        <Reveal delay={0.1}>
          <div className="mb-16">
            <div className="mb-6 flex items-center gap-3">
              <span className="h-px w-8 bg-gold/70" />
              <span className="label-hud text-gold">VOYAGE TIMELINE MATRIX</span>
            </div>
            <h3 className="display-title text-2xl sm:text-3xl text-white mb-8">EXPEDITION PHASES</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {VOYAGE_PHASES.map((phase, idx) => (
                <div key={phase.phase} className="p-6 rounded-2xl border border-card-border/90 bg-surface/75 hover:border-gold/60 hover:-translate-y-1 transition-all duration-300 relative group">
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-gold px-2.5 py-1 rounded-full bg-gold/10 border border-gold/30">
                      {phase.phase}
                    </span>
                    <span className="text-xs font-mono text-steel-500">0{idx + 1}/04</span>
                  </div>
                  <h4 className="font-display font-bold text-white text-base mb-2 group-hover:text-gold transition-colors">
                    {phase.title}
                  </h4>
                  <p className="text-xs text-steel-400 leading-relaxed">{phase.body}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Ops Desk & Communication */}
        <Reveal delay={0.2}>
          <div className="wano-scroll-frame p-6 sm:p-8">
            <PanelHeader
              kicker="COMMAND COMMUNICATIONS"
              title="DEN DEN MUSHI & OPS DESK CHANNELS"
              right={
                <span className="chip text-cyber-green border-cyber-green/30 bg-cyber-green/10">
                  CHANNELS ONLINE
                </span>
              }
            />
            <div className="hair-line-gold my-6" />

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {SOCIAL_LINKS.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.label}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-4 rounded-2xl border border-card-border bg-void/80 hover:border-gold hover:bg-surface transition-all flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl border border-gold/30 bg-gold/10 text-gold group-hover:scale-110 transition-transform">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="font-mono text-xs font-bold text-steel-200 group-hover:text-white">
                        {item.label}
                      </span>
                    </div>
                    <ExternalLink className="h-3.5 w-3.5 text-steel-500 group-hover:text-gold" />
                  </a>
                );
              })}
            </div>
          </div>
        </Reveal>
      </SectionShell>
    </div>
  );
};
