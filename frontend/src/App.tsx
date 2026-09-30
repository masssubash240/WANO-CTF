import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Challenges } from './pages/Challenges';
import { Scoreboard } from './pages/Scoreboard';
import { TeamPage } from './pages/Team';
import { Announcements } from './pages/Announcements';
import { Admin } from './pages/Admin';
import { Rules } from './pages/Rules';
import { About } from './pages/About';
import { SITE, SOCIAL_LINKS } from './lib/warzone';

const PAGE_VARIANTS = {
  hidden: { opacity: 0, y: 18, filter: 'blur(6px)' },
  visible: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -12, filter: 'blur(4px)', transition: { duration: 0.3 } },
};

const AnimatedRoutes: React.FC = () => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={PAGE_VARIANTS}
        initial="hidden"
        animate="visible"
        exit="exit"
        className="flex-1"
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/challenges" element={<Challenges />} />
          <Route path="/scoreboard" element={<Scoreboard />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/about" element={<About />} />
          <Route path="/team" element={<TeamPage />} />
          <Route path="/teams" element={<TeamPage />} />
          <Route path="/announcements" element={<Announcements />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-background text-steel-200 font-sans selection:bg-primary/30 selection:text-white">
          <Navbar />

          <main className="flex-1">
            <AnimatedRoutes />
          </main>

          {/* Tactical Cyber HUD Footer */}
          <footer className="border-t border-card-border/80 bg-void/90 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              {/* Brand column */}
              <div className="md:col-span-2 space-y-3">
                <Link to="/" className="inline-block group">
                  <img
                    src="/logo.png"
                    alt="CYBITRIDIC WANO FEST"
                    className="h-14 w-auto object-contain filter drop-shadow-[0_0_12px_rgba(43,127,255,0.4)] group-hover:scale-105 transition-transform"
                  />
                </Link>
                <p className="text-xs text-steel-400 max-w-sm leading-relaxed">
                  The collegiate digital warzone engineered for offensive and defensive operations. Enumerate, exploit, and defend against the clock.
                </p>
                <div className="flex items-center gap-4 text-xs font-mono text-steel-500 pt-2">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyber-green animate-pulse" />
                    <span>SYSTEMS OPERATIONAL</span>
                  </span>
                  <span>•</span>
                  <span>BUILD v2.6.4-WARZONE</span>
                </div>
              </div>

              {/* Navigation column */}
              <div>
                <div className="label-hud mb-3 text-steel-400">NAVIGATION</div>
                <ul className="space-y-2 text-xs font-mono text-steel-400">
                  <li>
                    <Link to="/challenges" className="hover:text-accent transition-colors">
                      TARGET ARSENAL
                    </Link>
                  </li>
                  <li>
                    <Link to="/scoreboard" className="hover:text-accent transition-colors">
                      LEADERBOARD
                    </Link>
                  </li>
                  <li>
                    <Link to="/rules" className="hover:text-accent transition-colors">
                      RULES OF ENGAGEMENT
                    </Link>
                  </li>
                  <li>
                    <Link to="/about" className="hover:text-accent transition-colors">
                      MISSION INTEL
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Social Channels */}
              <div>
                <div className="label-hud mb-3 text-steel-400">COMMUNICATIONS</div>
                <div className="flex flex-wrap gap-2">
                  {SOCIAL_LINKS.slice(0, 4).map((link) => {
                    const Icon = link.icon;
                    return (
                      <a
                        key={link.label}
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded-lg border border-card-border bg-surface/60 hover:border-accent hover:text-accent text-steel-400 transition-colors"
                        title={link.label}
                      >
                        <Icon className="h-4 w-4" />
                      </a>
                    );
                  })}
                </div>
                <div className="mt-3 text-[11px] font-mono text-steel-500">
                  Direct support:{' '}
                  <a href={`mailto:${SITE.supportEmail}`} className="text-accent hover:underline">
                    {SITE.supportEmail}
                  </a>
                </div>
              </div>
            </div>

            <div className="max-w-7xl mx-auto pt-6 border-t border-card-border/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-steel-500">
              <div>
                {SITE.name} &copy; 2026 • {SITE.org} • All Rights Reserved.
              </div>
              <div className="flex items-center gap-1">
                <span>SECURED WITH SHA-256 SALTED PEPPER ENGINE</span>
              </div>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};
