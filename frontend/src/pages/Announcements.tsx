import React, { useState, useEffect } from 'react';
import {
  Bell,
  Pin,
  Radio,
  Search,
  Info,
} from 'lucide-react';
import { Announcement } from '../types';
import { api } from '../lib/api';
import { formatStamp } from '../lib/warzone';

export const Announcements: React.FC = () => {
  const [items, setItems] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api
      .get<Announcement[]>('/announcements')
      .then((data) => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const body = (item: Announcement) => item.message || item.content || '';

  const filtered = items.filter(
    (i) =>
      i.title.toLowerCase().includes(search.toLowerCase()) ||
      body(i).toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative min-h-screen pb-24 pt-6">
      {/* Background subtle radial gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background -z-10" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-6 border-b border-card-border/60">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="h-px w-8 bg-accent/70" />
              <span className="label-hud text-accent">BROADCAST FREQUENCY</span>
            </div>
            <h1 className="display-title text-3xl sm:text-4xl text-white flex items-center gap-3">
              <Radio className="h-8 w-8 text-primary animate-pulse" />
              <span>COMMAND BROADCASTS</span>
            </h1>
            <p className="mt-1 text-xs text-steel-400">
              Live operational bulletins, hint releases, and system notices.
            </p>
          </div>

          <span className="chip border-cyber-green/40 text-cyber-green text-xs font-mono">
            FEED SYNCHRONIZED
          </span>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative w-full">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-steel-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search dispatches & bulletins..."
              className="w-full pl-10 pr-4 py-2 bg-void/80 border border-line rounded-xl font-mono text-xs text-slate-100 placeholder-steel-600 focus:outline-none focus:border-accent/60 transition-all"
            />
          </div>
        </div>

        {/* Broadcasts List */}
        {loading ? (
          <div className="py-20 text-center">
            <div className="inline-block animate-spin h-8 w-8 border-2 border-accent border-t-transparent rounded-full mb-3" />
            <div className="font-mono text-sm text-steel-400">TUNING FREQUENCIES...</div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-card-border bg-surface/30">
            <Bell className="h-10 w-10 text-steel-500 mx-auto mb-3" />
            <div className="font-mono text-base font-bold text-white mb-1">NO BROADCASTS RECEIVED</div>
            <p className="text-xs text-steel-400 max-w-sm mx-auto">
              All frequencies are clear. System bulletins will stream here as the competition progresses.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((item) => {
              const dateStr = item.published_at || item.created_at;
              return (
                <div
                  key={item.id}
                  className={`p-6 rounded-2xl border transition-all ${
                    item.is_pinned
                      ? 'border-amber-500/50 bg-amber-950/15 shadow-hud'
                      : 'border-card-border/80 bg-surface/60 hover:border-accent/40'
                  }`}
                >
                  <div className="flex items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2.5">
                      {item.is_pinned ? (
                        <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          <Pin className="h-4 w-4" />
                        </span>
                      ) : (
                        <span className="p-1.5 rounded-lg bg-primary/10 text-primary border border-primary/20">
                          <Info className="h-4 w-4" />
                        </span>
                      )}
                      <h3 className="font-display font-bold text-base sm:text-lg text-white">
                        {item.title}
                      </h3>
                    </div>

                    <span className="font-mono text-[11px] text-steel-400 shrink-0">
                      {formatStamp(dateStr as string)}
                    </span>
                  </div>

                  <div className="text-sm text-steel-200 font-sans leading-relaxed whitespace-pre-wrap pl-1">
                    {body(item)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
