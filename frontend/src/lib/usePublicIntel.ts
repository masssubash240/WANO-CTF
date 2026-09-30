import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Category, Challenge, CompetitionState, ScoreboardResponse } from '../types';

export interface PublicIntel {
  categories: Category[];
  challenges: Challenge[];
  scoreboard: ScoreboardResponse | null;
  competition: CompetitionState | null;
  loading: boolean;
  lastSync: number | null;
  refresh: () => Promise<void>;
}

const EMPTY: Pick<PublicIntel, 'categories' | 'challenges' | 'scoreboard' | 'competition'> = {
  categories: [],
  challenges: [],
  scoreboard: null,
  competition: null,
};

/**
 * One shared read of the public operations feed (categories, challenge index,
 * standings, competition state). Used by the landing console so the hero, event
 * intel, module grid and leaderboard render from a single poll instead of four.
 */
export function usePublicIntel(pollMs = 30_000): PublicIntel {
  const [state, setState] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState<number | null>(null);
  const alive = useRef(true);

  const refresh = useCallback(async () => {
    const [categories, challenges, scoreboard, competition] = await Promise.allSettled([
      api.get<Category[]>('/challenges/categories'),
      api.get<Challenge[]>('/challenges'),
      api.get<ScoreboardResponse>('/scoreboard'),
      api.get<CompetitionState>('/competition'),
    ]);
    if (!alive.current) return;

    setState((prev) => ({
      categories: categories.status === 'fulfilled' && Array.isArray(categories.value)
        ? categories.value
        : prev.categories,
      challenges: challenges.status === 'fulfilled' && Array.isArray(challenges.value)
        ? challenges.value
        : prev.challenges,
      scoreboard: scoreboard.status === 'fulfilled' ? scoreboard.value : prev.scoreboard,
      competition: competition.status === 'fulfilled' ? competition.value : prev.competition,
    }));
    setLastSync(Date.now());
    setLoading(false);
  }, []);

  useEffect(() => {
    alive.current = true;
    void refresh();
    if (pollMs <= 0) {
      return () => {
        alive.current = false;
      };
    }
    const timer = window.setInterval(() => void refresh(), pollMs);
    return () => {
      alive.current = false;
      window.clearInterval(timer);
    };
  }, [refresh, pollMs]);

  return { ...state, loading, lastSync, refresh };
}
