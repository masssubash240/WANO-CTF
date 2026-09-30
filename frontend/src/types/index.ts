export interface User {
  id: string;
  email: string;
  full_name: string;
  college?: string | null;
  department?: string | null;
  year?: string | null;
  phone?: string | null;
  role: string;
  email_verified: boolean;
  is_active: boolean;
  is_banned: boolean;
}

export interface SessionResponse {
  profile: User;
  team: TeamMembershipSummary | null;
  is_captain: boolean;
  is_admin: boolean;
  auth_provider: string;
  permissions: Record<string, boolean>;
}

export interface TeamMembershipSummary {
  id: string;
  name: string;
  team_code?: string | null;
  status: string;
  score: number;
  rank?: number | null;
  solved_count: number;
  hint_penalty: number;
  member_count: number;
  max_team_size: number;
  role: 'captain' | 'member';
  is_captain: boolean;
  members_locked: boolean;
  members: TeamMember[];
}

export interface TeamMember {
  id: string;
  user_id: string;
  role: 'captain' | 'member';
  joined_at?: string | null;
  display_name: string;
  college?: string | null;
}

export interface Team {
  id: string;
  name: string;
  team_code?: string | null;
  captain_id: string;
  captain_name?: string | null;
  college?: string | null;
  status: string;
  score: number;
  solved_count: number;
  member_count: number;
  last_solve_at?: string | null;
  members: TeamMember[];
  is_captain: boolean;
  members_locked: boolean;
}

export interface ChallengeHint {
  id: string;
  display_order: number;
  cost: number;
  is_unlocked: boolean;
  text?: string | null;
}

export interface ChallengeFile {
  id: string;
  filename: string;
  label?: string | null;
  size_bytes: number;
  mime_type: string;
  sha256?: string | null;
  download_url: string;
}

export interface Challenge {
  id: string;
  title: string;
  slug: string;
  category_slug: string;
  category_name: string;
  category_icon: string;
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  points: number;
  solved_count: number;
  is_solved: boolean;
  hint_count: number;
  file_count: number;
  author?: string | null;
  /** Detail-only fields */
  description?: string;
  connection_info?: string | null;
  flag_format_hint?: string | null;
  hints?: ChallengeHint[];
  files?: ChallengeFile[];
  attempts_used?: number;
  max_attempts?: number | null;
  attempts_remaining?: number | null;
  solved_at?: string | null;
  points_awarded?: number | null;
  first_blood?: boolean;
  /** Legacy aliases kept for templates that predate the backend contract */
  category?: string;
  solve_count?: number;
  unlocked?: boolean;
  content?: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  icon: string;
  accent: string;
  display_order: number;
  challenge_count: number;
  solved_count: number;
  total_points: number;
}

export interface ScoreboardEntry {
  rank: number;
  team_id?: string | null;
  team_name: string;
  college?: string | null;
  score: number;
  solved_count: number;
  last_solve_at?: string | null;
  member_count: number;
  is_own_team: boolean;
}

export interface ScoreboardResponse {
  entries: ScoreboardEntry[];
  total_teams: number;
  frozen: boolean;
  public: boolean;
  generated_at: string;
  my_team?: ScoreboardEntry | null;
}

export interface Announcement {
  id: string;
  title: string;
  message: string;
  priority: string;
  is_pinned: boolean;
  published_at?: string | null;
  author_name?: string | null;
  is_read: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  /** Legacy alias */
  content?: string;
}

export interface CompetitionState {
  name: string;
  status: 'upcoming' | 'live' | 'paused' | 'ended';
  start_at?: string | null;
  end_at?: string | null;
  server_time: string;
  seconds_remaining?: number | null;
  seconds_until_start?: number | null;
  elapsed_seconds?: number | null;
  registration_open: boolean;
  submissions_enabled: boolean;
  teams_locked: boolean;
  scoreboard_public: boolean;
  /** Legacy alias used by older templates */
  submissions_open?: boolean;
}
