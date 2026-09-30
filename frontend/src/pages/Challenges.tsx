import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  CheckCircle2,
  AlertCircle,
  Send,
  Download,
  Link2,
  Copy,
  Check,
  Unlock,
  Lock,
  X,
  Compass,
  Map as MapIcon,
  LayoutGrid,
  Swords,
  Terminal,
} from 'lucide-react';
import { Challenge, Category } from '../types';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { resolveCategoryIcon, formatCount } from '../lib/warzone';
import { ThreatPips } from '../components/warzone/ui';

const ISLAND_DESIGNATIONS: Record<string, { islandName: string; region: string; iconBg: string }> = {
  web: { islandName: 'Enies Lobby Port', region: 'Sector 01', iconBg: 'border-blue-500/30 bg-blue-950/20 text-blue-400' },
  crypto: { islandName: 'Poneglyph Cipher Vault', region: 'Sector 02', iconBg: 'border-gold/30 bg-gold/15 text-gold' },
  osint: { islandName: 'Den Den Mushi Grid', region: 'Sector 03', iconBg: 'border-amber-500/30 bg-amber-950/20 text-amber-400' },
  forensics: { islandName: 'Log Pose Artifacts', region: 'Sector 04', iconBg: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-400' },
  linux: { islandName: 'Iron Kernel Citadel', region: 'Sector 05', iconBg: 'border-purple-500/30 bg-purple-950/20 text-purple-400' },
  reverse: { islandName: 'Vegapunk Decompilations', region: 'Sector 06', iconBg: 'border-crimson/30 bg-crimson/15 text-crimson-glow' },
  networking: { islandName: 'All Blue Stream', region: 'Sector 07', iconBg: 'border-cyan-500/30 bg-cyan-950/20 text-cyan-400' },
  misc: { islandName: 'Grand Line Anomalies', region: 'Sector 08', iconBg: 'border-pink-500/30 bg-pink-950/20 text-pink-400' },
};

function categoryLabel(ch: Challenge): string {
  return ch.category_name || ch.category || 'Misc';
}

export const Challenges: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [selectedCat, setSelectedCat] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'unsolved' | 'solved'>('all');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');

  // Modal detail
  const [modal, setModal] = useState<Challenge | null>(null);
  const [flag, setFlag] = useState('');
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hintBusy, setHintBusy] = useState<string | null>(null);
  const [copiedHost, setCopiedHost] = useState(false);

  const { user } = useAuth();

  useEffect(() => {
    Promise.all([
      api.get<Category[]>('/challenges/categories').catch(() => [] as Category[]),
      api.get<Challenge[]>('/challenges').catch(() => [] as Challenge[]),
    ]).then(([cats, challs]) => {
      setCategories(Array.isArray(cats) ? cats : []);
      setChallenges(Array.isArray(challs) ? challs : []);
      setLoading(false);
    });
  }, []);

  const openChallenge = async (ch: Challenge) => {
    setModal(ch);
    setStatus(null);
    setFlag('');
    try {
      const detail = await api.get<Challenge>(`/challenges/${ch.slug}`);
      setModal(detail);
      setChallenges((prev) =>
        prev.map((c) => (c.id === detail.id ? { ...c, is_solved: detail.is_solved } : c))
      );
    } catch {
      // keep summary card
    }
  };

  const submitFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modal || !flag.trim()) return;
    if (!user) {
      setStatus({ ok: false, msg: 'Authentication required. Please sign in to submit flags.' });
      return;
    }
    setSubmitting(true);
    setStatus(null);
    try {
      const res = await api.post<{
        correct: boolean;
        message: string;
        points_awarded: number;
        already_solved: boolean;
      }>(`/submissions/${modal.slug}/submit`, { flag: flag.trim() });

      setStatus({ ok: true, msg: `BOUNTY CLAIMED! ${res.message} (+${res.points_awarded} pts)` });
      setChallenges((prev) =>
        prev.map((c) => (c.id === modal.id ? { ...c, is_solved: true } : c))
      );
      setModal((prev) => (prev ? { ...prev, is_solved: true } : null));
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : 'Incorrect flag or invalid ciphertext hash.';
      setStatus({ ok: false, msg });
    } finally {
      setSubmitting(false);
    }
  };

  const unlockHint = async (hintId: string) => {
    if (!modal) return;
    setHintBusy(hintId);
    try {
      const res = await api.post<{ hint_id: string; text: string; cost_paid: number }>(
        `/challenges/${modal.slug}/hints/${hintId}/unlock`
      );
      setModal((prev) =>
        prev
          ? {
              ...prev,
              hints: (prev.hints || []).map((h) =>
                h.id === hintId ? { ...h, is_unlocked: true, text: res.text } : h
              ),
            }
          : null
      );
      setStatus({ ok: true, msg: `Poneglyph fragment decoded. (-${res.cost_paid} pts penalty deducted)` });
    } catch (err: unknown) {
      setStatus({ ok: false, msg: err instanceof ApiError ? err.message : 'Unable to decode hint.' });
    } finally {
      setHintBusy(null);
    }
  };

  const copyConnectionInfo = () => {
    if (modal?.connection_info) {
      navigator.clipboard.writeText(modal.connection_info);
      setCopiedHost(true);
      setTimeout(() => setCopiedHost(false), 2000);
    }
  };

  const totalPoints = challenges.reduce((acc, c) => acc + (c.points || 0), 0);
  const userScore = challenges
    .filter((c) => c.is_solved)
    .reduce((acc, c) => acc + (c.points || 0), 0);

  // Category counts
  const catCountMap = useMemo(() => {
    const map: Record<string, { total: number; solved: number }> = {};
    challenges.forEach((ch) => {
      const slug = (ch.category_slug || ch.category || 'misc').toLowerCase();
      if (!map[slug]) map[slug] = { total: 0, solved: 0 };
      map[slug].total += 1;
      if (ch.is_solved) map[slug].solved += 1;
    });
    return map;
  }, [challenges]);

  // Filtering
  const filteredList = useMemo(() => {
    return challenges.filter((c) => {
      const slug = (c.category_slug || c.category || '').toLowerCase();
      const matchCat = selectedCat === 'all' || slug === selectedCat.toLowerCase();
      const matchDiff =
        selectedDifficulty === 'all' ||
        (c.difficulty || '').toLowerCase() === selectedDifficulty.toLowerCase();
      const matchStatus =
        statusFilter === 'all' ||
        (statusFilter === 'solved' ? c.is_solved : !c.is_solved);
      const matchSearch =
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        (c.description || '').toLowerCase().includes(search.toLowerCase()) ||
        slug.includes(search.toLowerCase()) ||
        (c.author || '').toLowerCase().includes(search.toLowerCase());

      return matchCat && matchDiff && matchStatus && matchSearch;
    });
  }, [challenges, selectedCat, selectedDifficulty, statusFilter, search]);

  return (
    <div className="relative min-h-screen pb-24 pt-6">
      {/* Background blood moon & oceanic haze */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(224,47,62,0.12),_transparent_60%)] -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Telemetry Bar */}
        <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-card-border/80">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="h-px w-8 bg-gold/70" />
              <span className="label-hud text-gold">GRAND LINE SECTOR MAP</span>
            </div>
            <h1 className="display-title text-3xl sm:text-4xl text-white flex items-center gap-3">
              <Compass className="h-8 w-8 text-gold" />
              <span>THE GRAND LINE — CHALLENGE MAP</span>
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-steel-400">
              Liberate islands across the Grand Line, retrieve ancient flags, and build your pirate bounty.
            </p>
          </div>

          {/* Quick Stats & View Switcher */}
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-void/80 border border-card-border p-1 rounded-xl">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
                  viewMode === 'grid' ? 'bg-gold text-black font-bold' : 'text-steel-400 hover:text-white'
                }`}
                title="Tactical Grid View"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">GRID</span>
              </button>
              <button
                onClick={() => setViewMode('map')}
                className={`p-2 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
                  viewMode === 'map' ? 'bg-gold text-black font-bold' : 'text-steel-400 hover:text-white'
                }`}
                title="Grand Line Island Map"
              >
                <MapIcon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">ISLAND MAP</span>
              </button>
            </div>

            {/* Bounty Counter Pill */}
            <div className="bg-surface/80 border border-gold/40 px-4 py-2 rounded-xl backdrop-blur-md font-mono text-xs shadow-glow-gold">
              <div className="label-hud text-gold text-[9px]">SQUAD BOUNTY</div>
              <div className="font-bold text-white text-sm">
                ฿ {formatCount(userScore)} <span className="text-steel-500 font-normal">/ {formatCount(totalPoints)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Search & Island Filter Controls */}
        <div className="mb-6 space-y-4">
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-between">
            {/* Search Input */}
            <div className="relative w-full sm:max-w-md">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-steel-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search islands by name, author or vulnerability..."
                className="w-full pl-10 pr-4 py-2 bg-void/90 border border-line rounded-xl font-mono text-xs text-slate-100 placeholder-steel-600 focus:outline-none focus:border-gold/60 transition-all"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-3 top-2.5 text-steel-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Dropdowns */}
            <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="bg-void/90 border border-line rounded-xl px-3 py-2 font-mono text-xs text-steel-300 focus:outline-none focus:border-gold"
              >
                <option value="all">ALL THREAT LEVELS</option>
                <option value="easy">LOW (EASY)</option>
                <option value="medium">GUARDED (MEDIUM)</option>
                <option value="hard">ELEVATED (HARD)</option>
                <option value="expert">SEVERE (EXPERT)</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="bg-void/90 border border-line rounded-xl px-3 py-2 font-mono text-xs text-steel-300 focus:outline-none focus:border-gold"
              >
                <option value="all">ALL STATUSES</option>
                <option value="unsolved">UNCONQUERED ISLANDS</option>
                <option value="solved">LIBERATED ISLANDS</option>
              </select>
            </div>
          </div>

          {/* 8 Island Categories Filter Bar */}
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
            <button
              onClick={() => setSelectedCat('all')}
              className={`px-4 py-2 rounded-xl font-mono text-xs uppercase font-bold flex items-center gap-2 shrink-0 transition-all ${
                selectedCat === 'all'
                  ? 'bg-gold text-black shadow-glow-gold'
                  : 'bg-surface/70 border border-card-border text-steel-300 hover:text-white hover:border-gold/40'
              }`}
            >
              <span>ALL ISLANDS</span>
              <span className="text-[10px] opacity-75">({challenges.length})</span>
            </button>

            {categories.map((c) => {
              const Icon = resolveCategoryIcon(c.icon, c.slug);
              const stats = catCountMap[c.slug.toLowerCase()] || { total: 0, solved: 0 };
              const isSelected = selectedCat.toLowerCase() === c.slug.toLowerCase();

              return (
                <button
                  key={c.id}
                  onClick={() => setSelectedCat(c.slug)}
                  className={`px-3.5 py-2 rounded-xl font-mono text-xs uppercase font-bold flex items-center gap-2 shrink-0 transition-all ${
                    isSelected
                      ? 'bg-crimson text-white shadow-glow-crimson border border-crimson-glow'
                      : 'bg-surface/70 border border-card-border text-steel-300 hover:text-white hover:border-crimson/40'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{c.name}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isSelected ? 'bg-black/30 text-white' : 'bg-void text-steel-400'
                  }`}>
                    {stats.solved}/{stats.total}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ---------------------------------------------------- INTERACTIVE ISLAND MAP VIEW */}
        {viewMode === 'map' && (
          <div className="mb-10 p-6 sm:p-8 rounded-3xl border border-gold/40 bg-gradient-to-b from-[#08121f] via-void to-[#050b14] relative overflow-hidden shadow-wanted">
            <div className="absolute inset-0 bg-[radial-gradient(#e5a93c_1px,transparent_1px)] [background-size:28px_28px] opacity-10 pointer-events-none" />
            
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Compass className="h-5 w-5 text-gold animate-spin-slow" />
                <span className="font-display font-bold text-sm text-gold tracking-widest uppercase">
                  GRAND LINE LOG POSE NAVIGATION
                </span>
              </div>
              <span className="label-hud text-accent font-mono">SECTORS 01 — 08</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(ISLAND_DESIGNATIONS).map(([slug, info]) => {
                const Icon = resolveCategoryIcon(slug, slug);
                const stats = catCountMap[slug] || { total: 0, solved: 0 };
                const isSelected = selectedCat.toLowerCase() === slug;

                return (
                  <div
                    key={slug}
                    onClick={() => setSelectedCat(slug)}
                    className={`p-4 rounded-2xl border cursor-pointer transition-all duration-300 ${
                      isSelected
                        ? 'border-gold bg-gold/15 shadow-glow-gold scale-102'
                        : 'border-card-border/80 bg-surface/60 hover:border-gold/40 hover:bg-surface/90'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="label-hud text-crimson text-[9px]">{info.region}</span>
                      <span className="font-mono text-[10px] text-steel-400 font-bold">
                        {stats.solved}/{stats.total} LIBERATED
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-xl border ${info.iconBg}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-display font-bold text-sm text-white">{info.islandName}</h4>
                        <div className="text-[11px] font-mono text-gold uppercase">{slug} security</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ---------------------------------------------------- CHALLENGES GRID */}
        {loading ? (
          <div className="py-24 text-center">
            <div className="inline-block animate-spin h-8 w-8 border-2 border-gold border-t-transparent rounded-full mb-3" />
            <div className="font-mono text-sm text-steel-400">CALCULATING LOG POSE COORDINATES...</div>
          </div>
        ) : filteredList.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-card-border bg-surface/30">
            <Compass className="h-10 w-10 text-steel-500 mx-auto mb-3" />
            <div className="font-mono text-base font-bold text-white mb-1">NO TARGET ISLANDS LOCATED</div>
            <p className="text-xs text-steel-400 max-w-sm mx-auto">
              No challenges match your current search query or sector filter.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredList.map((ch) => {
              const Icon = resolveCategoryIcon(ch.category_slug, ch.category_slug);
              const isSolved = ch.is_solved;
              const islandInfo = ISLAND_DESIGNATIONS[(ch.category_slug || '').toLowerCase()];

              return (
                <div
                  key={ch.id}
                  onClick={() => openChallenge(ch)}
                  className={`group relative rounded-2xl border p-5 cursor-pointer transition-all duration-300 ${
                    isSolved
                      ? 'border-cyber-green/50 bg-cyber-green/[0.04] hover:border-cyber-green shadow-[0_0_18px_rgba(47,211,164,0.15)]'
                      : 'border-card-border/90 bg-surface/75 hover:border-gold/70 hover:-translate-y-1 hover:shadow-glow-gold'
                  }`}
                >
                  {/* Top Bar: Island Tag + Bounty Points */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded-lg border border-gold/30 bg-gold/10 text-gold group-hover:scale-110 transition-transform">
                        <Icon className="h-3.5 w-3.5" />
                      </span>
                      <span className="label-hud text-gold font-bold">
                        {islandInfo ? islandInfo.islandName : categoryLabel(ch)}
                      </span>
                    </div>
                    <span className="font-mono text-xs font-bold text-white px-2.5 py-0.5 rounded-full border border-card-border bg-void/90">
                      ฿ {ch.points}
                    </span>
                  </div>

                  {/* Challenge Name & Solved Indicator */}
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="font-display font-bold text-base text-white group-hover:text-gold transition-colors line-clamp-1">
                      {ch.title}
                    </h3>
                    {isSolved && (
                      <span className="flex items-center gap-1 text-cyber-green font-mono text-xs font-bold shrink-0">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>CAPTURED</span>
                      </span>
                    )}
                  </div>

                  {/* Mission Brief Narrative */}
                  <p className="text-xs text-steel-400 line-clamp-2 mb-4 leading-relaxed">
                    {ch.description || 'Access target brief for mission directives and connection specs.'}
                  </p>

                  {/* Footer: Threat Pips + Author + Launch Button */}
                  <div className="flex items-center justify-between pt-3 border-t border-card-border/60 text-xs font-mono">
                    <ThreatPips difficulty={ch.difficulty} />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openChallenge(ch);
                      }}
                      className="px-2.5 py-1 rounded-lg border border-card-border bg-void text-[11px] text-steel-300 group-hover:border-gold group-hover:text-gold transition-colors flex items-center gap-1"
                    >
                      <Swords className="h-3 w-3" />
                      <span>{isSolved ? 'REVIEW' : 'LAUNCH'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ---------------------------------------------------- CHALLENGE DETAIL MODAL */}
        {modal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/85 backdrop-blur-xl">
            <div className="w-full max-w-4xl bg-surface border border-gold/40 rounded-3xl shadow-wanted p-6 sm:p-8 relative max-h-[92vh] overflow-y-auto">
              {/* Close Button */}
              <button
                onClick={() => setModal(null)}
                className="absolute top-5 right-5 p-2 rounded-xl border border-card-border text-steel-400 hover:text-white hover:border-gold transition-colors"
                title="Close Mission Brief"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Modal Header */}
              <div className="flex items-center gap-2 mb-2">
                <span className="label-hud text-gold">
                  {categoryLabel(modal)}
                </span>
                <span className="text-steel-600">•</span>
                <ThreatPips difficulty={modal.difficulty} />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-card-border">
                <div>
                  <h2 className="display-title text-2xl sm:text-3xl text-white">
                    {modal.title}
                  </h2>
                  <div className="text-xs font-mono text-steel-400 mt-1">
                    TARGET ARCHIPELAGO: <span className="text-gold font-bold">{ISLAND_DESIGNATIONS[(modal.category_slug || '').toLowerCase()]?.islandName || 'Grand Line Bastion'}</span>
                  </div>
                </div>
                <span className="font-mono text-base font-bold text-gold px-4 py-1.5 rounded-xl border border-gold/40 bg-gold/10 shrink-0 self-start sm:self-auto">
                  ฿ {modal.points} BOUNTY
                </span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Mission Objective & Clues */}
                <div className="lg:col-span-7 space-y-4">
                  {/* Objective Description */}
                  <div>
                    <div className="label-hud mb-1.5 text-steel-400">MISSION DIRECTIVE</div>
                    <div className="p-4 rounded-2xl border border-card-border bg-void/80 text-steel-200 text-xs sm:text-sm font-sans leading-relaxed whitespace-pre-wrap">
                      {modal.description || 'Target brief details are classified. Initiate connection to inspect.'}
                    </div>
                  </div>

                  {/* Target Connection Host */}
                  {modal.connection_info && (
                    <div>
                      <div className="label-hud mb-1.5 text-steel-400">TARGET CONNECTION ENDPOINT</div>
                      <div className="p-3 rounded-xl bg-void border border-primary/30 flex items-center justify-between gap-3 font-mono text-xs">
                        <div className="flex items-center gap-2 text-steel-200 truncate">
                          <Link2 className="h-4 w-4 text-accent shrink-0" />
                          <span className="truncate select-all">{modal.connection_info}</span>
                        </div>
                        <button
                          onClick={copyConnectionInfo}
                          className="px-2.5 py-1 rounded-lg border border-card-border text-steel-300 hover:text-white hover:border-accent text-[11px] flex items-center gap-1 shrink-0 transition-colors"
                        >
                          {copiedHost ? <Check className="h-3 w-3 text-cyber-green" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedHost ? 'COPIED' : 'COPY'}</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Download Artifacts */}
                  {modal.files && modal.files.length > 0 && (
                    <div>
                      <div className="label-hud mb-1.5 text-steel-400">DOWNLOADABLE LOG ARTIFACTS</div>
                      <div className="flex flex-wrap gap-2">
                        {modal.files.map((file) => (
                          <a
                            key={file.id}
                            href={file.download_url}
                            download
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-card-border bg-void/80 hover:border-gold/60 text-xs font-mono text-gold transition-all"
                          >
                            <Download className="h-3.5 w-3.5" />
                            <span>{file.filename}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Hints Decrypter */}
                  {modal.hints && modal.hints.length > 0 && (
                    <div className="space-y-2">
                      <div className="label-hud text-steel-400">PONEGLYPH INTEL / HINTS</div>
                      {modal.hints.map((hint, idx) => (
                        <div
                          key={hint.id}
                          className="p-3 rounded-xl border border-card-border bg-void/70 text-xs font-mono"
                        >
                          {hint.is_unlocked || hint.text ? (
                            <div className="text-steel-200">
                              <span className="text-gold font-bold mr-2">[CLUE 0{idx + 1}]</span>
                              {hint.text}
                            </div>
                          ) : (
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-2 text-steel-400">
                                <Lock className="h-3.5 w-3.5 text-amber-500" />
                                <span>ENCRYPTED CLUE 0{idx + 1} (Cost: -{hint.cost} PTS)</span>
                              </div>
                              <button
                                onClick={() => unlockHint(hint.id)}
                                disabled={hintBusy === hint.id}
                                className="hud-btn-ghost py-1 px-3 text-[11px] disabled:opacity-50"
                              >
                                <Unlock className="h-3 w-3" />
                                <span>{hintBusy === hint.id ? 'DECRYPTING...' : 'UNLOCK CLUE'}</span>
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column: Flag Submission Terminal */}
                <div className="lg:col-span-5 flex flex-col justify-between">
                  <div className="p-5 rounded-2xl border border-gold/40 bg-void/95 font-mono text-xs shadow-glow-gold">
                    <div className="flex items-center gap-2 pb-3 border-b border-card-border mb-4">
                      <Terminal className="h-4 w-4 text-gold" />
                      <span className="text-steel-300 font-bold">root@wano-ctf:~$ submit_flag</span>
                    </div>

                    <form onSubmit={submitFlag} className="space-y-4">
                      <div>
                        <label className="field-label text-gold">CAPTURE FLAG INPUT</label>
                        <input
                          type="text"
                          value={flag}
                          onChange={(e) => setFlag(e.target.value)}
                          placeholder="WANO{ENTER_YOUR_FLAG_HERE}"
                          disabled={modal.is_solved}
                          className="w-full px-4 py-3 bg-surface border border-line rounded-xl font-mono text-xs text-white placeholder-steel-600 focus:outline-none focus:border-gold transition-all disabled:opacity-50"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={submitting || modal.is_solved || !flag.trim()}
                        className="hud-btn-gold w-full py-3 text-xs font-bold disabled:opacity-50"
                      >
                        <Send className="h-4 w-4" />
                        <span>{submitting ? 'TRANSMITTING...' : 'CAPTURE FLAG'}</span>
                      </button>

                      {/* Status feedback */}
                      {status && (
                        <div
                          className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2 ${
                            status.ok
                              ? 'border-cyber-green/50 bg-cyber-green/10 text-cyber-green'
                              : 'border-crimson/50 bg-crimson/10 text-crimson-glow'
                          }`}
                        >
                          {status.ok ? (
                            <CheckCircle2 className="h-4 w-4 shrink-0 text-cyber-green" />
                          ) : (
                            <AlertCircle className="h-4 w-4 shrink-0 text-crimson" />
                          )}
                          <span>{status.msg}</span>
                        </div>
                      )}
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
