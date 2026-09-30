import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Flag,
  Trophy,
  Users,
  LogOut,
  Shield,
  FileText,
  Menu,
  X,
  Info,
  Compass,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatCount } from '../lib/warzone';

export const Navbar: React.FC = () => {
  const { user, team, isAdmin, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const teamName = team?.name;

  const navLinks = [
    { name: 'HOME', path: '/', icon: Compass },
    { name: 'CHALLENGES', path: '/challenges', icon: Flag },
    { name: 'LEADERBOARD', path: '/scoreboard', icon: Trophy },
    { name: 'RULES', path: '/rules', icon: FileText },
    { name: 'ABOUT', path: '/about', icon: Info },
    ...(user ? [{ name: 'MY CREW', path: '/team', icon: Users }] : []),
  ];

  return (
    <header className="sticky top-0 z-50 backdrop-blur-2xl bg-void/85 border-b border-card-border/80 shadow-hud">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Brand Logo & Connection Status */}
          <div className="flex items-center space-x-3 sm:space-x-5">
            <Link to="/" className="flex items-center gap-2 group">
              <img
                src="/logo.png"
                alt="CYBITRIDIC WANO FEST"
                className="h-10 sm:h-12 w-auto object-contain filter drop-shadow-[0_0_12px_rgba(229,169,60,0.5)] group-hover:drop-shadow-[0_0_20px_rgba(224,47,62,0.8)] group-hover:scale-105 transition-all duration-300"
              />
            </Link>

            {/* Connection Live Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-void/90 border border-cyber-green/40 shadow-[0_0_12px_rgba(47,211,164,0.15)]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyber-green opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyber-green" />
              </span>
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-cyber-green">
                CONNECTION: ONLINE
              </span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold tracking-wider transition-all duration-300 ${
                    isActive
                      ? 'bg-gradient-to-r from-gold/15 to-crimson/15 text-gold border border-gold/40 shadow-glow-gold'
                      : 'text-steel-300 hover:text-white hover:bg-card/60 hover:border-slate-600'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Action: Player Profile / Auth */}
          <div className="flex items-center space-x-3">
            {user ? (
              <div className="flex items-center space-x-3">
                {/* Player Avatar & Bounty */}
                <div className="flex items-center gap-3 bg-surface/80 border border-card-border px-3 py-1.5 rounded-xl">
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-gold/30 to-crimson/30 border border-gold/50 flex items-center justify-center font-display font-bold text-xs text-gold">
                    {(user.full_name || user.email)[0].toUpperCase()}
                  </div>
                  <div className="text-left hidden sm:block">
                    <div className="text-xs font-bold text-white font-display truncate max-w-[110px]">
                      {user.full_name || user.email.split('@')[0]}
                    </div>
                    <div className="text-[10px] text-gold font-mono font-bold flex items-center gap-1">
                      <span>฿ {formatCount(team?.score || 0)}</span>
                      {teamName && <span className="text-steel-400">[{teamName}]</span>}
                    </div>
                  </div>
                </div>

                {isAdmin && (
                  <Link
                    to="/admin"
                    className="px-2.5 py-1.5 rounded-xl bg-crimson/20 border border-crimson/40 text-crimson hover:bg-crimson/30 transition-all text-xs font-mono font-bold flex items-center space-x-1 shadow-glow-crimson"
                  >
                    <Shield className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">WAR ROOM</span>
                  </Link>
                )}

                <button
                  onClick={logout}
                  title="Abandon Ship (Logout)"
                  className="p-2 rounded-xl border border-card-border text-steel-400 hover:text-crimson hover:border-crimson/40 hover:bg-card transition-all"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="hidden sm:flex items-center space-x-2 font-mono text-xs">
                <Link
                  to="/login"
                  className="px-4 py-2 text-steel-300 hover:text-white hover:bg-card rounded-xl transition-all"
                >
                  LOG IN
                </Link>
                <Link
                  to="/register"
                  className="hud-btn-gold py-2 px-4 text-xs shadow-glow-gold"
                >
                  <span>JOIN CREW</span>
                </Link>
              </div>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-xl border border-card-border text-steel-300 hover:text-white"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileOpen && (
        <div className="lg:hidden border-b border-card-border bg-void/95 p-4 space-y-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-xl text-xs font-mono font-bold ${
                  isActive
                    ? 'bg-gold/15 text-gold border border-gold/40'
                    : 'text-steel-300 hover:bg-card'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{link.name}</span>
              </Link>
            );
          })}

          {!user && (
            <div className="pt-3 border-t border-card-border flex flex-col gap-2 font-mono text-xs">
              <Link
                to="/login"
                onClick={() => setMobileOpen(false)}
                className="w-full text-center py-2.5 rounded-xl border border-card-border text-steel-300"
              >
                LOG IN
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileOpen(false)}
                className="w-full text-center py-2.5 rounded-xl bg-gold text-black font-bold"
              >
                JOIN CREW
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
