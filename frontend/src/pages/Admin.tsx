import React, { useState, useEffect } from 'react';
import {
  Shield,
  Plus,
  Radio,
  Flame,
  Users,
  Target,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { api, ApiError } from '../lib/api';
import { Challenge } from '../types';
import { HudFrame, PanelHeader, MetricCard, ThreatPips } from '../components/warzone/ui';

export const Admin: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);

  // Deploy Target Form
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [category, setCategory] = useState('web');
  const [difficulty, setDifficulty] = useState('medium');
  const [points, setPoints] = useState(100);
  const [flag, setFlag] = useState('');
  const [connectionInfo, setConnectionInfo] = useState('');
  const [description, setDescription] = useState('');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // Broadcast Form
  const [bcTitle, setBcTitle] = useState('');
  const [bcContent, setBcContent] = useState('');
  const [bcPinned, setBcPinned] = useState(false);
  const [bcMsg, setBcMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const loadAll = async () => {
    try {
      const [st, challs] = await Promise.all([
        api.get('/admin/stats').catch(() => null),
        api.get<Challenge[]>('/challenges').catch(() => [] as Challenge[]),
      ]);
      setStats(st);
      setChallenges(Array.isArray(challs) ? challs : []);
    } catch {
      // silent
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleCreateChallenge = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('/admin/challenges', {
        title,
        slug: slug || undefined,
        category_slug: category,
        points: Number(points),
        flag,
        description,
        difficulty,
        connection_info: connectionInfo || undefined,
        visible: true,
      });
      setMsg({ ok: true, text: 'Target deployed into active challenge grid successfully!' });
      setTitle('');
      setSlug('');
      setFlag('');
      setConnectionInfo('');
      setDescription('');
      loadAll();
    } catch (err: unknown) {
      setMsg({
        ok: false,
        text: err instanceof ApiError ? err.message : 'Error deploying target challenge.',
      });
    }
  };

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    setBcMsg(null);
    try {
      await api.post('/admin/announcements', {
        title: bcTitle,
        content: bcContent,
        is_pinned: bcPinned,
      });
      setBcMsg({ ok: true, text: 'Dispatch broadcasted across live channels!' });
      setBcTitle('');
      setBcContent('');
      setBcPinned(false);
    } catch (err: unknown) {
      setBcMsg({
        ok: false,
        text: err instanceof ApiError ? err.message : 'Error broadcasting bulletin.',
      });
    }
  };

  return (
    <div className="relative min-h-screen pb-24 pt-6">
      {/* Background subtle radial gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-red-950/20 via-background to-background -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 font-mono">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between pb-6 border-b border-card-border/60">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="h-px w-8 bg-red-500/70" />
              <span className="label-hud text-red-400">OPS DESK CONSOLE</span>
            </div>
            <h1 className="display-title text-3xl sm:text-4xl text-white flex items-center gap-3">
              <Shield className="h-8 w-8 text-red-500" />
              <span>WAR ROOM COMMAND</span>
            </h1>
            <p className="mt-1 text-xs text-steel-400">
              Competition management, target deployment, and real-time telemetry control.
            </p>
          </div>

          <span className="chip border-red-500/40 bg-red-950/20 text-red-400 text-xs">
            ADMIN CLEARANCE HIGH
          </span>
        </div>

        {/* Telemetry Metrics */}
        {stats && (
          <div className="mb-10 grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            <MetricCard
              label="TOTAL CADETS"
              value={stats.total_participants || 0}
              hint="Registered operators"
              icon={Users}
              tone="blue"
            />
            <MetricCard
              label="ACTIVE SQUADS"
              value={stats.total_teams || 0}
              hint="Formed teams"
              icon={Shield}
              tone="cyan"
            />
            <MetricCard
              label="TARGET ARSENAL"
              value={stats.total_challenges || 0}
              hint="Deployed challenges"
              icon={Target}
              tone="blue"
            />
            <MetricCard
              label="TRANSMISSIONS"
              value={stats.total_submissions || 0}
              hint="Flag submissions logged"
              icon={Flame}
              tone="alert"
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
          {/* Target Deployment Form */}
          <div className="lg:col-span-7">
            <HudFrame className="p-6 sm:p-8">
              <PanelHeader
                kicker="TARGET DEPLOYMENT"
                title="DEPLOY NEW CHALLENGE"
                right={
                  <span className="p-2 rounded-xl bg-primary/10 border border-primary/30 text-primary">
                    <Plus className="h-5 w-5" />
                  </span>
                }
              />
              <div className="hair-line my-4" />

              {msg && (
                <div
                  className={`p-3 rounded-xl border text-xs mb-4 flex items-center gap-2 ${
                    msg.ok
                      ? 'border-emerald-500/40 bg-emerald-950/40 text-emerald-400'
                      : 'border-red-500/40 bg-red-950/40 text-red-400'
                  }`}
                >
                  {msg.ok ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
                  <span>{msg.text}</span>
                </div>
              )}

              <form onSubmit={handleCreateChallenge} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="field-label">TARGET TITLE</label>
                    <input
                      type="text"
                      required
                      value={title}
                      onChange={(e) => {
                        setTitle(e.target.value);
                        if (!slug) setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
                      }}
                      placeholder="e.g. Vault Infiltration"
                      className="field-input"
                    />
                  </div>

                  <div>
                    <label className="field-label">UNIQUE SLUG</label>
                    <input
                      type="text"
                      value={slug}
                      onChange={(e) => setSlug(e.target.value)}
                      placeholder="e.g. vault-infiltration"
                      className="field-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="field-label">CATEGORY</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="field-input cursor-pointer"
                    >
                      <option value="web">Web Exploitation</option>
                      <option value="crypto">Cryptography</option>
                      <option value="reverse">Reverse Engineering</option>
                      <option value="forensics">Digital Forensics</option>
                      <option value="binary">Binary PWN</option>
                      <option value="osint">OSINT</option>
                      <option value="misc">Miscellaneous</option>
                    </select>
                  </div>

                  <div>
                    <label className="field-label">THREAT LEVEL</label>
                    <select
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                      className="field-input cursor-pointer"
                    >
                      <option value="easy">Low (Easy)</option>
                      <option value="medium">Guarded (Medium)</option>
                      <option value="hard">Elevated (Hard)</option>
                      <option value="expert">Severe (Expert)</option>
                    </select>
                  </div>

                  <div>
                    <label className="field-label">POINTS AWARD</label>
                    <input
                      type="number"
                      required
                      value={points}
                      onChange={(e) => setPoints(Number(e.target.value))}
                      className="field-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="field-label">FLAG SECRET (HASHED)</label>
                    <input
                      type="text"
                      required
                      value={flag}
                      onChange={(e) => setFlag(e.target.value)}
                      placeholder="WANO{flag_secret_here}"
                      className="field-input"
                    />
                  </div>

                  <div>
                    <label className="field-label">CONNECTION HOST:PORT</label>
                    <input
                      type="text"
                      value={connectionInfo}
                      onChange={(e) => setConnectionInfo(e.target.value)}
                      placeholder="nc target.wano-fest.com 1337"
                      className="field-input"
                    />
                  </div>
                </div>

                <div>
                  <label className="field-label">MISSION DIRECTIVE / DESCRIPTION</label>
                  <textarea
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Provide the challenge brief, scenario, clues, or background context..."
                    className="field-input resize-none"
                  />
                </div>

                <button type="submit" className="hud-btn-primary w-full text-xs">
                  <span>DEPLOY TARGET TO ARSENAL</span>
                </button>
              </form>
            </HudFrame>
          </div>

          {/* Dispatch Announcement Form */}
          <div className="lg:col-span-5">
            <HudFrame className="p-6 sm:p-8">
              <PanelHeader
                kicker="TACTICAL BROADCAST"
                title="DISPATCH BULLETIN"
                right={
                  <span className="p-2 rounded-xl bg-accent/10 border border-accent/30 text-accent">
                    <Radio className="h-5 w-5" />
                  </span>
                }
              />
              <div className="hair-line my-4" />

              {bcMsg && (
                <div
                  className={`p-3 rounded-xl border text-xs mb-4 flex items-center gap-2 ${
                    bcMsg.ok
                      ? 'border-emerald-500/40 bg-emerald-950/40 text-emerald-400'
                      : 'border-red-500/40 bg-red-950/40 text-red-400'
                  }`}
                >
                  {bcMsg.ok ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
                  <span>{bcMsg.text}</span>
                </div>
              )}

              <form onSubmit={handleBroadcast} className="space-y-4 text-xs">
                <div>
                  <label className="field-label">BULLETIN TITLE</label>
                  <input
                    type="text"
                    required
                    value={bcTitle}
                    onChange={(e) => setBcTitle(e.target.value)}
                    placeholder="e.g. Hint Unlocked for Web Target #3"
                    className="field-input"
                  />
                </div>

                <div>
                  <label className="field-label">BULLETIN CONTENT</label>
                  <textarea
                    rows={4}
                    required
                    value={bcContent}
                    onChange={(e) => setBcContent(e.target.value)}
                    placeholder="Enter broadcast message text..."
                    className="field-input resize-none"
                  />
                </div>

                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={bcPinned}
                    onChange={(e) => setBcPinned(e.target.checked)}
                    className="accent-cyan-400 rounded cursor-pointer"
                  />
                  <span className="text-steel-300 font-bold">PIN AS HIGH-PRIORITY ALERT</span>
                </label>

                <button type="submit" className="hud-btn-ghost w-full text-xs">
                  <span>DISPATCH BROADCAST</span>
                </button>
              </form>
            </HudFrame>
          </div>
        </div>

        {/* Live Targets Table */}
        <HudFrame className="p-6">
          <PanelHeader
            kicker="ACTIVE TARGETS"
            title="DEPLOYED TARGET INVENTORY"
            right={
              <span className="font-mono text-xs text-accent">
                {challenges.length} TARGETS
              </span>
            }
          />
          <div className="hair-line my-4" />

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-void/80 border-b border-card-border uppercase text-steel-400 font-mono">
                <tr>
                  <th className="py-3 px-4">TITLE</th>
                  <th className="py-3 px-4">CATEGORY</th>
                  <th className="py-3 px-4">DIFFICULTY</th>
                  <th className="py-3 px-4">POINTS</th>
                  <th className="py-3 px-4">SOLVES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border/60 font-mono">
                {challenges.map((c) => (
                  <tr key={c.id} className="hover:bg-card/40">
                    <td className="py-3 px-4 font-bold text-white">{c.title}</td>
                    <td className="py-3 px-4 text-accent uppercase">{c.category_name || c.category || 'Misc'}</td>
                    <td className="py-3 px-4"><ThreatPips difficulty={c.difficulty} /></td>
                    <td className="py-3 px-4 font-bold text-white">{c.points} PTS</td>
                    <td className="py-3 px-4 text-steel-400">{c.solved_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </HudFrame>
      </div>
    </div>
  );
};
