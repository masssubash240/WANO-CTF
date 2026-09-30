import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, CompetitionState, SessionResponse, TeamMembershipSummary } from '../types';
import { api } from '../lib/api';

interface AuthContextType {
  user: User | null;
  session: SessionResponse | null;
  team: TeamMembershipSummary | null;
  isAdmin: boolean;
  token: string | null;
  competition: CompetitionState | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshCompetition: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [competition, setCompetition] = useState<CompetitionState | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setSession(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const current = localStorage.getItem('token');
    if (!current) {
      setUser(null);
      setSession(null);
      return;
    }
    try {
      const data = await api.get<SessionResponse>('/users/me');
      setSession(data);
      setUser(data.profile);
    } catch {
      logout();
    }
  }, [logout]);

  const refreshCompetition = useCallback(async () => {
    try {
      const data = await api.get<CompetitionState>('/competition');
      setCompetition({ ...data, submissions_open: data.submissions_enabled });
    } catch {
      // competition status fallback
      setCompetition({
        name: 'WANO CTF',
        status: 'live',
        server_time: new Date().toISOString(),
        registration_open: true,
        submissions_enabled: true,
        submissions_open: true,
        teams_locked: false,
        scoreboard_public: true,
      });
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await Promise.allSettled([refreshUser(), refreshCompetition()]);
      setIsLoading(false);
    };
    init();
  }, [token, refreshUser, refreshCompetition]);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        team: session?.team ?? null,
        isAdmin: session?.is_admin ?? false,
        token,
        competition,
        isLoading,
        login,
        logout,
        refreshUser,
        refreshCompetition,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
