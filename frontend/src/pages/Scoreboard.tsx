import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Search,
  Flame,
  Snowflake,
  Crown,
} from 'lucide-react';
import { ScoreboardEntry, ScoreboardResponse } from '../types';
import { api } from '../lib/api';
import { formatCount } from '../lib/warzone';
import { LiveDot, Reveal } from '../components/warzone/ui';

export const Scoreboard: React.FC = () => {
  const [entries, setEntries] = useState<ScoreboardEntry[]>([]);
  const [frozen, setFrozen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadScores = async () => {
    setLoading(true);
    try {
      const data = await api.get<ScoreboardResponse>('/scoreboard');
      setEntries(Array.isArray(data.entries) ? data.entries : []);
      setFrozen(Boolean(data.frozen));
      setLastRefreshed(new Date());
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScores();
    if (!autoRefresh) return;
    const interval = setInterval(loadScores, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const filteredEntries = entries.filter((e) =>
    (e.team_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (e.college || '').toLowerCase().includes(search.toLowerCase())
  );

  const top3 = entries.slice(0, 3);

  return (
    <div className="relative min-h-screen pb-24 pt-6">
      {/* Subtle Blood Moon & Ocean Haze */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(229,169,60,0.12),_transparent_60%)] -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Bar */}
        <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-card-border/80">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="h-px w-8 bg-gold/70" />
              <span className="label-hud text-gold">GRAND LINE BOUNTY MANIFEST</span>
            </div>
            <h1 className="display-title text-3xl sm:text-4xl text-white flex items-center gap-3">
              <Crown className="h-8 w-8 text-gold animate-bounce" />
              <span>WANTED — TOP PIRATES</span>
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-steel-400">
              Official World Government bounties and live crew rankings across the Grand Line.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3.5 py-2 rounded-xl border font-mono text-xs flex items-center gap-2 transition-all ${
                autoRefresh
                  ? 'border-cyber-green/40 bg-cyber-green/10 text-cyber-green'
                  : 'border-card-border bg-void text-steel-400'
              }`}
            >
              <LiveDot label={autoRefresh ? 'RADAR LIVE' : 'RADAR PAUSED'} tone={autoRefresh ? 'green' : 'cyan'} />
            </button>

            <button
              onClick={loadScores}
              disabled={loading}
              className="p-2.5 rounded-xl border border-card-border bg-surface/80 text-steel-300 hover:text-white hover:border-gold transition-all disabled:opacity-50"
              title="Manual sync"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-gold' : ''}`} />
            </button>
          </div>
        </div>

        {/* Frozen Alert Banner */}
        {frozen && (
          <div className="mb-8 p-4 rounded-2xl border border-cyan-500/40 bg-cyan-950/30 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-accent">
                <Snowflake className="h-5 w-5 animate-pulse" />
              </div>
              <div>
                <div className="font-display font-bold text-white text-sm">LOG POSE FROZEN</div>
                <div className="text-xs text-steel-300">
                  Scoreboard is frozen for the final escalation window. All captures are recorded silently.
                </div>
              </div>
            </div>
            <span className="chip border-accent/40 text-accent font-bold">FROZEN</span>
          </div>
        )}

        {/* ------------------------------------------------ TOP 3 FUTURISTIC WANTED POSTERS */}
        {entries.length >= 3 && (
          <Reveal>
            <div className="mb-12 grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
              {/* Silver #2 Wanted Poster */}
              <div className="order-2 md:order-1 wanted-card border-slate-400/50 hover:border-slate-300">
                <div className="wanted-banner text-slate-300 text-xs">
                  ★ WANTED — DEAD OR ALIVE ★
                </div>
                <div className="text-center py-4 border-b border-card-border/60">
                  <div className="h-16 w-16 mx-auto mb-3 rounded-2xl bg-slate-800/80 border border-slate-400/50 flex items-center justify-center font-display font-black text-2xl text-slate-300 shadow-hud">
                    #2
                  </div>
                  <h3 className="font-display font-extrabold text-xl text-white truncate mb-1">
                    {top3[1].team_name}
                  </h3>
                  <div className="text-xs font-mono text-steel-400 truncate">
                    {top3[1].college || 'Grand Line Armada'}
                  </div>
                </div>
                <div className="pt-4 text-center">
                  <div className="label-hud text-slate-400 text-[10px]">CURRENT BOUNTY</div>
                  <div className="text-2xl font-black font-mono text-slate-200 mt-1">
                    ฿ {formatCount(top3[1].score)}
                  </div>
                  <div className="text-[11px] font-mono text-steel-400 mt-1">
                    {top3[1].solved_count} Islands Liberated
                  </div>
                </div>
              </div>

              {/* Gold #1 Wanted Poster (Pirate King) */}
              <div className="order-1 md:order-2 wanted-card border-gold bg-gradient-to-b from-[#141b26] via-surface to-[#0d141e] shadow-glow-gold scale-105 -translate-y-3">
                <div className="wanted-banner text-gold text-sm font-black animate-pulse">
                  ☠ PIRATE KING — WANTED ☠
                </div>
                <div className="text-center py-5 border-b border-gold/30">
                  <div className="h-20 w-20 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-gold/30 to-crimson/30 border border-gold flex items-center justify-center font-display font-black text-3xl text-gold shadow-glow-gold">
                    <Crown className="h-10 w-10 text-gold" />
                  </div>
                  <h3 className="font-display font-black text-2xl text-white truncate mb-1 text-glow-gold">
                    {top3[0].team_name}
                  </h3>
                  <div className="text-xs font-mono text-gold font-semibold truncate">
                    {top3[0].college || 'Supreme Yonko Fleet'}
                  </div>
                </div>
                <div className="pt-4 text-center">
                  <div className="label-hud text-gold text-[10px] tracking-widest">HIGHEST BOUNTY ON GRAND LINE</div>
                  <div className="text-3xl font-black font-mono text-gold mt-1 text-glow-gold">
                    ฿ {formatCount(top3[0].score)}
                  </div>
                  <div className="text-xs font-mono text-gold/90 mt-1 font-bold">
                    {top3[0].solved_count} Islands Liberated
                  </div>
                </div>
              </div>

              {/* Bronze #3 Wanted Poster */}
              <div className="order-3 wanted-card border-amber-700/50 hover:border-amber-600">
                <div className="wanted-banner text-amber-500 text-xs">
                  ★ WANTED — DEAD OR ALIVE ★
                </div>
                <div className="text-center py-4 border-b border-card-border/60">
                  <div className="h-16 w-16 mx-auto mb-3 rounded-2xl bg-amber-950/60 border border-amber-600/50 flex items-center justify-center font-display font-black text-2xl text-amber-500 shadow-hud">
                    #3
                  </div>
                  <h3 className="font-display font-extrabold text-xl text-white truncate mb-1">
                    {top3[2].team_name}
                  </h3>
                  <div className="text-xs font-mono text-steel-400 truncate">
                    {top3[2].college || 'Warlord Syndicate'}
                  </div>
                </div>
                <div className="pt-4 text-center">
                  <div className="label-hud text-amber-500 text-[10px]">CURRENT BOUNTY</div>
                  <div className="text-2xl font-black font-mono text-amber-400 mt-1">
                    ฿ {formatCount(top3[2].score)}
                  </div>
                  <div className="text-[11px] font-mono text-steel-400 mt-1">
                    {top3[2].solved_count} Islands Liberated
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        )}

        {/* Search Bar */}
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-steel-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search pirate crew or college..."
              className="w-full pl-10 pr-4 py-2.5 bg-void/90 border border-line rounded-xl font-mono text-xs text-slate-100 placeholder-steel-600 focus:outline-none focus:border-gold/60 transition-all"
            />
          </div>
          <div className="text-xs font-mono text-steel-500 hidden sm:block">
            Radar sync: {lastRefreshed.toLocaleTimeString()}
          </div>
        </div>

        {/* ---------------------------------------------------- WANTED MANIFEST TABLE */}
        <div className="rounded-3xl border border-gold/30 bg-surface/80 shadow-wanted overflow-hidden backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-void/95 border-b border-card-border font-mono text-xs uppercase text-gold">
                <tr>
                  <th className="py-4 px-6 w-20 text-center">RANK</th>
                  <th className="py-4 px-6">PIRATE CREW / VESSEL</th>
                  <th className="py-4 px-6 text-center">ISLANDS SOLVED</th>
                  <th className="py-4 px-6 text-right">BOUNTY (SCORE)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border/60 font-mono text-xs">
                {loading && entries.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-16 text-center text-steel-500 font-mono">
                      SYNCHRONIZING DEN DEN MUSHI BOUNTY FEED...
                    </td>
                  </tr>
                ) : filteredEntries.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-16 text-center text-steel-500 font-mono">
                      NO REGISTERED CAPTURES IN LOG POSE ARCHIVE YET.
                    </td>
                  </tr>
                ) : (
                  filteredEntries.map((entry, idx) => {
                    const rank = idx + 1;
                    return (
                      <tr
                        key={entry.team_id || idx}
                        className="hover:bg-gold/5 transition-colors"
                      >
                        <td className="py-4 px-6 text-center">
                          {rank === 1 ? (
                            <span className="inline-flex p-1.5 rounded-lg bg-gold/20 text-gold font-bold">
                              #1
                            </span>
                          ) : rank === 2 ? (
                            <span className="inline-flex p-1.5 rounded-lg bg-slate-400/20 text-slate-300 font-bold">
                              #2
                            </span>
                          ) : rank === 3 ? (
                            <span className="inline-flex p-1.5 rounded-lg bg-amber-600/20 text-amber-500 font-bold">
                              #3
                            </span>
                          ) : (
                            <span className="text-steel-500 font-semibold">#{rank}</span>
                          )}
                        </td>
                        <td className="py-4 px-6">
                          <div className="font-display font-bold text-white text-sm">
                            {entry.team_name}
                          </div>
                          {entry.college && (
                            <div className="text-[11px] text-steel-400 font-mono">
                              {entry.college}
                            </div>
                          )}
                        </td>
                        <td className="py-4 px-6 text-center text-steel-300">
                          <span className="inline-flex items-center gap-1.5">
                            <Flame className="h-3.5 w-3.5 text-gold" />
                            <span>{entry.solved_count} captures</span>
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right font-black text-gold text-sm">
                          ฿ {formatCount(entry.score)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
