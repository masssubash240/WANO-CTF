import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Lock,
  Mail,
  User,
  AlertCircle,
  ArrowRight,
  School,
  BookOpen,
  Calendar,
  Users,
  Crown,
} from 'lucide-react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [college, setCollege] = useState('');
  const [department, setDepartment] = useState('');
  const [year, setYear] = useState('1st Year');
  const [teamName, setTeamName] = useState('');
  const [isTeamLeader, setIsTeamLeader] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await api.post<{ access_token: string }>('/auth/register', {
        email,
        full_name: fullName,
        password,
        college,
        department,
        year,
        team_name: isTeamLeader && teamName.trim() ? teamName.trim() : undefined,
        is_team_leader: isTeamLeader,
      });

      localStorage.setItem('token', data.access_token);
      const session = await api.get<{ profile: any }>('/users/me');

      login(data.access_token, session.profile);
      navigate(session.profile?.team ? '/challenges' : '/team');
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Enrollment transaction rejected. Check all required parameters.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <div className="wano-scroll-frame p-8 sm:p-10 shadow-glow-gold">
          {/* Header Logo */}
          <div className="text-center mb-6">
            <img
              src="/logo.png"
              alt="CYBITRIDIC WANO FEST"
              className="h-16 sm:h-20 w-auto mx-auto mb-3 object-contain filter drop-shadow-[0_0_20px_rgba(229,169,60,0.6)]"
            />
            <div className="label-hud text-gold">GRAND LINE CADET INDUCTION</div>
            <h2 className="font-display font-extrabold text-xl text-white tracking-wide mt-1">
              PIRATE CREW ENROLLMENT
            </h2>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-xl border border-crimson/40 bg-crimson/10 text-crimson-glow text-xs font-mono flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-crimson" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="field-label text-gold">CADET FULL NAME</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Mercer"
                    className="field-input pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="field-label text-gold">ACADEMIC EMAIL</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="cadet@college.edu"
                    className="field-input pl-10"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="field-label text-gold">ACCESS CIPHER / PASSWORD</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="field-input pl-10"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="field-label text-gold">COLLEGE / INSTITUTION</label>
                <div className="relative">
                  <School className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                  <input
                    type="text"
                    required
                    value={college}
                    onChange={(e) => setCollege(e.target.value)}
                    placeholder="e.g. IIT Madras / PSG Tech"
                    className="field-input pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="field-label text-gold">DEPARTMENT / MAJOR</label>
                <div className="relative">
                  <BookOpen className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                  <input
                    type="text"
                    required
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. Computer Science"
                    className="field-input pl-10"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="field-label text-gold">ACADEMIC YEAR</label>
              <div className="relative">
                <Calendar className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                <select
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="field-input pl-10 cursor-pointer"
                >
                  <option value="1st Year">1st Year</option>
                  <option value="2nd Year">2nd Year</option>
                  <option value="3rd Year">3rd Year</option>
                  <option value="4th Year">4th Year</option>
                  <option value="Postgraduate">Postgraduate</option>
                </select>
              </div>
            </div>

            {/* Captain Toggle */}
            <div className="p-4 rounded-2xl border border-gold/30 bg-void/70 space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isTeamLeader}
                  onChange={(e) => setIsTeamLeader(e.target.checked)}
                  className="h-4 w-4 accent-amber-400 rounded cursor-pointer"
                />
                <div className="flex items-center gap-2">
                  <Crown className="h-4 w-4 text-gold" />
                  <span className="font-mono text-xs font-bold text-white">
                    I AM COMMISSIONING A CREW AS CAPTAIN
                  </span>
                </div>
              </label>

              {isTeamLeader && (
                <div className="pt-2">
                  <label className="field-label text-gold">INITIAL CREW / VESSEL NAME</label>
                  <div className="relative">
                    <Users className="absolute left-3.5 top-3 h-4 w-4 text-steel-500" />
                    <input
                      type="text"
                      required={isTeamLeader}
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      placeholder="e.g. STRAWH4T_CYBER"
                      className="field-input pl-10"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="hud-btn-gold w-full text-xs font-bold disabled:opacity-50"
              >
                <span>{loading ? 'ENROLLING CADET...' : 'COMPLETE CREW ENROLLMENT'}</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>

          <div className="mt-8 pt-6 border-t border-card-border/60 text-center font-mono text-xs text-steel-400">
            <span>Already enrolled as an operative? </span>
            <Link to="/login" className="text-gold font-bold hover:underline">
              Sign In to Terminal
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
