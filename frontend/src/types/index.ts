/**
 * Type definitions for InstantMusic frontend
 */

export interface User {
  id: number;
  username: string;
  email: string;
  avatar?: string;
  total_games_played: number;
  total_wins: number;
  total_points: number;
  win_rate: number;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password2: string;
}

export type GameMode = 'classique' | 'rapide' | 'generation' | 'paroles' | 'karaoke';
export type GameStatus = 'waiting' | 'in_progress' | 'finished' | 'cancelled';
export type AnswerMode = 'mcq' | 'text';
export type GuessTarget = 'artist' | 'title';

export interface Game {
  id: string;
  name?: string;
  room_code: string;
  host: number;
  host_username: string;
  mode: GameMode;
  status: GameStatus;
  max_players: number;
  num_rounds: number;
  playlist_id?: string;
  karaoke_track?: KaraokeTrack | null;
  is_online: boolean;
  answer_mode: AnswerMode;
  guess_target: GuessTarget;
  round_duration: number;
  timer_start_round: number;
  score_display_duration: number;
  lyrics_words_count: number;
  players: GamePlayer[];
  player_count: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
}

export interface GamePlayer {
  id: number;
  user: number;
  username: string;
  avatar?: string;
  score: number;
  rank?: number;
  is_connected: boolean;
  joined_at: string;
}

export interface CreateGameData {
  name?: string;
  mode: GameMode;
  max_players: number;
  num_rounds: number;
  playlist_id?: string;
  karaoke_track?: KaraokeTrack | null;
  is_online: boolean;
  answer_mode: AnswerMode;
  guess_target: GuessTarget;
  round_duration: number;
  timer_start_round: number;
  score_display_duration: number;
  lyrics_words_count?: number;
}

/** Track selected for karaoke mode (single YouTube song). */
export interface KaraokeTrack {
  youtube_video_id: string;
  track_name: string;
  artist_name: string;
  duration_ms: number;
  album_image?: string;
}

export interface GameRound {
  id: number;
  game: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  preview_url?: string;
  options: string[];
  question_type: string;
  question_text: string;
  extra_data: Record<string, any>;
  duration: number;
  started_at: string;
  ended_at?: string;
}

export interface GameAnswer {
  round: number;
  answer: string;
  response_time: number;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// YouTube / Playlist types
export interface YouTubePlaylist {
  youtube_id: string;
  name: string;
  description: string;
  image_url: string;
  total_tracks: number;
  owner: string;
  external_url: string;
}

export interface YouTubeTrack {
  youtube_id: string;
  name: string;
  artists: string[];
  album: string;
  album_image: string;
  duration_ms: number;
  preview_url: string | null;
  external_url: string;
}

export interface Playlist {
  id: number;
  youtube_id: string;
  name: string;
  description: string;
  image_url: string;
  total_tracks: number;
  owner: string;
  external_url: string;
  created_at: string;
  updated_at: string;
}

export interface Track {
  id: number;
  youtube_id: string;
  name: string;
  artists: string[];
  artists_display: string;
  album: string;
  album_image: string;
  duration_ms: number;
  preview_url: string | null;
  external_url: string;
  created_at: string;
  updated_at: string;
}

// Game History types
export interface GameParticipant {
  id: number;
  username: string;
  avatar: string | null;
  score: number;
  rank: number;
}

export interface GameWinner {
  id: number;
  username: string;
  avatar: string | null;
}

export interface GameHistory {
  id: string;
  room_code: string;
  host_username: string;
  mode: GameMode;
  mode_display: string;
  answer_mode: AnswerMode;
  answer_mode_display: string;
  guess_target: GuessTarget;
  guess_target_display: string;
  num_rounds: number;
  playlist_id: string | null;
  winner: GameWinner | null;
  winner_score: number;
  player_count: number;
  participants: GameParticipant[];
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

// Leaderboard types
export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  avatar: string | null;
  total_games: number;
  total_wins: number;
  total_points: number;
  win_rate: number;
  team_name?: string | null;
}

export interface TeamLeaderboardEntry {
  rank: number;
  team_id: number;
  name: string;
  avatar: string | null;
  owner_name: string | null;
  member_count: number;
  total_points: number;
  total_games: number;
  total_wins: number;
  win_rate: number;
}

export interface MyRank {
  general_rank: number;
  total_players: number;
  mode_ranks: Record<string, { rank: number; points: number; label: string }>;
}

// Friendship types
export type FriendshipStatus = 'pending' | 'accepted' | 'rejected';

export interface UserMinimal {
  id: number;
  username: string;
  avatar: string | null;
  total_points: number;
  total_wins: number;
}

export interface Friendship {
  id: number;
  from_user: UserMinimal;
  to_user: UserMinimal;
  status: FriendshipStatus;
  created_at: string;
  updated_at: string;
}

export interface Friend {
  friendship_id: number;
  user: UserMinimal;
  since: string;
}

// Team types
export type TeamMemberRole = 'owner' | 'admin' | 'member';

export interface TeamMember {
  id: number;
  user: UserMinimal;
  role: TeamMemberRole;
  joined_at: string;
}

export interface Team {
  id: number;
  name: string;
  description: string;
  avatar: string | null;
  owner: UserMinimal;
  members_list: TeamMember[];
  member_count: number;
  total_games: number;
  total_wins: number;
  total_points: number;
  created_at: string;
  updated_at: string;
}

// Achievement types
export interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string | null;
  points: number;
  condition_type: string;
  condition_value: number;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface UserAchievement {
  id: number;
  achievement: Achievement;
  unlocked_at: string;
}

// Stats types
export interface UserDetailedStats {
  total_games_played: number;
  total_wins: number;
  total_points: number;
  win_rate: number;
  avg_score_per_game: number;
  best_score: number;
  total_correct_answers: number;
  total_answers: number;
  accuracy: number;
  avg_response_time: number;
  achievements_unlocked: number;
  achievements_total: number;
  recent_games: GameHistory[];
}
