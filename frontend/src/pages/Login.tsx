import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Lock,
  Mail,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await api.post<{ access_token: string; refresh_token?: string }>(
        '/auth/login',
        {
          email,
          password,
        }
      );

      // Token response carries no profile — fetch the session, then store both.
      localStorage.setItem('token', data.access_token);
      const session = await api.get<{ profile: any }>('/users/me');

      login(data.access_token, session.profile);
      navigate('/challenges');
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Authentication handshake failed. Check your email and password.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="wano-scroll-frame p-8 sm:p-10 shadow-glow-gold">
          {/* Header Logo */}
          <div className="text-center mb-6">
            <img
              src="/logo.png"
              alt="CYBITRIDIC WANO FEST"
              className="h-16 sm:h-20 w-auto mx-auto mb-3 object-contain filter drop-shadow-[0_0_20px_rgba(229,169,60,0.6)]"
            />
            <div className="label-hud text-gold">GRAND LINE EXPEDITION ACCESS</div>
            <h2 className="font-display font-extrabold text-xl text-white tracking-wide mt-1">
              OPERATOR LOG IN
            </h2>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-xl border border-crimson/40 bg-crimson/10 text-crimson-glow text-xs font-mono flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-crimson" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="field-label text-gold">ACADEMIC / OPERATIVE EMAIL</label>
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

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="hud-btn-gold w-full text-xs font-bold disabled:opacity-50"
              >
                <span>{loading ? 'AUTHENTICATING...' : 'BOARD VESSEL (LOG IN)'}</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>

          <div className="mt-8 pt-6 border-t border-card-border/60 text-center font-mono text-xs text-steel-400">
            <span>New cadet operative? </span>
            <Link to="/register" className="text-gold font-bold hover:underline">
              Enroll Squad / Register
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
