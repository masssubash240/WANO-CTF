import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Copy,
  Check,
  Crown,
  ArrowRight,
  Anchor,
} from 'lucide-react';
import { Team } from '../types';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { formatCount } from '../lib/warzone';
import { PanelHeader, Reveal } from '../components/warzone/ui';

export const TeamPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);

  // Forms
  const [teamName, setTeamName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  const loadTeam = async () => {
    setLoading(true);
    try {
      const data = await api.get<Team>('/teams/mine');
      setTeam(data && (data as Team).id ? data : null);
    } catch {
      setTeam(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeam();
  }, [user]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamName.trim()) return;
    setStatus(null);
    setBusy(true);
    try {
      await api.post('/teams', { name: teamName.trim() });
      await refreshUser();
      await loadTeam();
      setStatus({ ok: true, msg: 'Pirate crew commissioned and vessel christened!' });
    } catch (err: unknown) {
      setStatus({
        ok: false,
        msg: err instanceof ApiError ? err.message : 'Failed to commission crew.',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!joinCode.trim()) return;
    setStatus(null);
    setBusy(true);
    try {
      await api.post('/teams/join', { team_code: joinCode.trim().toUpperCase() });
      await refreshUser();
      await loadTeam();
      setStatus({ ok: true, msg: 'Successfully boarded the pirate crew vessel!' });
    } catch (err: unknown) {
      setStatus({
        ok: false,
        msg: err instanceof ApiError ? err.message : 'Invalid crew passcode or vessel is full.',
      });
    } finally {
      setBusy(false);
    }
  };

  const copyCode = () => {
    if (team?.team_code) {
      navigator.clipboard.writeText(team.team_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin h-8 w-8 border-2 border-gold border-t-transparent rounded-full mb-3" />
          <div className="font-mono text-sm text-steel-400">RETRIEVING CREW LOG POSE...</div>
        </div>
      </div>
    );
  }

  // Not in a team yet
  if (!team) {
    return (
      <div className="relative min-h-[85vh] pb-24 pt-10 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-gold/40 bg-gold/10 text-gold text-xs font-mono uppercase mb-4 shadow-glow-gold">
              <Anchor className="h-3.5 w-3.5 text-gold" />
              <span>CREW COMMISSIONING</span>
            </div>
            <h1 className="display-title text-3xl sm:text-4xl text-white mb-2">
              COMMISSION OR BOARD A PIRATE CREW
            </h1>
            <p className="text-xs sm:text-sm text-steel-400 max-w-md mx-auto">
              Every cadet must belong to a registered crew to submit target flags and earn bounties across the Grand Line.
            </p>
          </div>

          {status && (
            <div
              className={`p-4 rounded-2xl border text-xs font-mono mb-8 max-w-2xl mx-auto flex items-center gap-2 ${
                status.ok
                  ? 'border-cyber-green/50 bg-cyber-green/10 text-cyber-green'
                  : 'border-crimson/50 bg-crimson/10 text-crimson-glow'
              }`}
            >
              <span>{status.msg}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Create Crew Panel */}
            <div className="wano-scroll-frame flex flex-col justify-between">
              <div>
                <PanelHeader
                  kicker="CAPTAIN INITIATIVE"
                  title="COMMISSION NEW CREW"
                  right={
                    <span className="p-2.5 rounded-xl bg-gold/10 border border-gold/30 text-gold">
                      <Crown className="h-5 w-5" />
                    </span>
                  }
                />
                <p className="mt-2 text-xs text-steel-300">
                  Form a new pirate crew as Captain. You will receive an exclusive crew passcode to invite your members.
                </p>

                <form onSubmit={handleCreate} className="mt-6 space-y-4">
                  <div>
                    <label className="field-label text-gold">CREW DESIGNATION / VESSEL NAME</label>
                    <input
                      type="text"
                      required
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      placeholder="e.g. STRAWH4T_PIRATES"
                      className="field-input"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={busy || !teamName.trim()}
                    className="hud-btn-gold w-full text-xs font-bold"
                  >
                    <span>{busy ? 'COMMISSIONING...' : 'CHRISTEN & COMMISSION'}</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </form>
              </div>
            </div>

            {/* Join Crew Panel */}
            <div className="wano-scroll-frame flex flex-col justify-between">
              <div>
                <PanelHeader
                  kicker="OPERATIVE BOARDING"
                  title="ENTER CREW PASSCODE"
                  right={
                    <span className="p-2.5 rounded-xl bg-accent/10 border border-accent/30 text-accent">
                      <UserPlus className="h-5 w-5" />
                    </span>
                  }
                />
                <p className="mt-2 text-xs text-steel-300">
                  Board an existing crew vessel using the unique passcode provided by your Captain.
                </p>

                <form onSubmit={handleJoin} className="mt-6 space-y-4">
                  <div>
                    <label className="field-label text-accent">CREW INVITATION PASSCODE</label>
                    <input
                      type="text"
                      required
                      value={joinCode}
                      onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                      placeholder="e.g. CREW-7X9"
                      className="field-input uppercase"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={busy || !joinCode.trim()}
                    className="hud-btn-ghost w-full text-xs font-bold"
                  >
                    <span>{busy ? 'BOARDING...' : 'BOARD VESSEL'}</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Active Team View
  const members = team.members || [];

  return (
    <div className="relative min-h-screen pb-24 pt-6">
      {/* Subtle background glow */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(229,169,60,0.12),_transparent_60%)] -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Crew Header Command Deck */}
        <Reveal>
          <div className="wano-scroll-frame mb-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-4 rounded-2xl border border-gold/50 bg-gold/10 text-gold shadow-glow-gold">
                  <Anchor className="h-8 w-8 text-gold" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="label-hud text-gold">PIRATE CREW COMMAND</span>
                    <span className="chip border-cyber-green/40 text-cyber-green text-[10px]">
                      VESSEL ACTIVE
                    </span>
                  </div>
                  <h1 className="display-title text-2xl sm:text-3xl text-white mt-1">
                    {team.name}
                  </h1>
                </div>
              </div>

              {/* Passcode Copy Box */}
              {team.team_code && (
                <div className="p-3.5 rounded-2xl border border-gold/40 bg-void/90 flex items-center gap-3 shadow-glow-gold">
                  <div>
                    <div className="label-hud text-gold text-[9px]">CREW INVITE PASSCODE</div>
                    <div className="font-mono text-sm font-bold text-white tracking-widest">
                      {team.team_code}
                    </div>
                  </div>
                  <button
                    onClick={copyCode}
                    className="p-2 rounded-xl border border-card-border hover:border-gold text-steel-300 hover:text-white transition-colors"
                    title="Copy crew invite passcode"
                  >
                    {copied ? <Check className="h-4 w-4 text-cyber-green" /> : <Copy className="h-4 w-4 text-gold" />}
                  </button>
                </div>
              )}
            </div>
          </div>
        </Reveal>

        {/* Telemetry Metrics */}
        <div className="mb-8 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl border border-gold/40 bg-surface/75 shadow-glow-gold">
            <div className="label-hud text-gold mb-1">TOTAL CREW BOUNTY</div>
            <div className="font-display font-black text-2xl sm:text-3xl text-gold font-mono">
              ฿ {formatCount(team.score || 0)}
            </div>
            <div className="mt-1 text-xs text-steel-400">Accumulated flag points</div>
          </div>

          <div className="p-6 rounded-2xl border border-accent/40 bg-surface/75">
            <div className="label-hud text-accent mb-1">ISLANDS CONQUERED</div>
            <div className="font-display font-black text-2xl sm:text-3xl text-accent font-mono">
              {team.solved_count || 0} CAPTURES
            </div>
            <div className="mt-1 text-xs text-steel-400">Validated challenge solves</div>
          </div>

          <div className="p-6 rounded-2xl border border-card-border bg-surface/75">
            <div className="label-hud text-steel-400 mb-1">CREW ROSTER CAPACITY</div>
            <div className="font-display font-black text-2xl sm:text-3xl text-white font-mono">
              {members.length} / 4 OPERATIVES
            </div>
            <div className="mt-1 text-xs text-steel-400">Active pirates on deck</div>
          </div>
        </div>

        {/* Member Roster */}
        <div className="max-w-3xl mx-auto">
          <div className="wano-scroll-frame p-6 sm:p-8">
            <PanelHeader
              kicker="CREW MANIFEST"
              title="REGISTERED PIRATES"
              right={
                <span className="font-mono text-xs text-gold font-bold">
                  {members.length} MEMBERS
                </span>
              }
            />
            <div className="hair-line-gold my-4" />

            <div className="space-y-3">
              {members.map((member, idx) => {
                const isCaptain = member.role === 'captain';
                return (
                  <div
                    key={member.id || idx}
                    className="p-4 rounded-2xl border border-card-border bg-void/80 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-surface border border-card-border text-steel-300">
                        {isCaptain ? (
                          <Crown className="h-5 w-5 text-gold animate-pulse" />
                        ) : (
                          <Users className="h-5 w-5 text-steel-400" />
                        )}
                      </div>
                      <div>
                        <div className="font-display font-bold text-sm text-white flex items-center gap-2">
                          <span>{member.display_name}</span>
                          {isCaptain && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-gold/20 text-gold border border-gold/40 font-bold">
                              CAPTAIN
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] font-mono text-steel-400">
                          {member.college || 'Cadet Operative'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
