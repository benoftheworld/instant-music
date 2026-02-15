/**
 * Type definitions for InstantMusic frontend
 */

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  bio?: string;
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
  first_name?: string;
  last_name?: string;
}

export type GameMode = 'quiz_4' | 'quiz_fastest' | 'karaoke';
export type GameStatus = 'waiting' | 'in_progress' | 'finished' | 'cancelled';

export interface Game {
  id: string;
  room_code: string;
  host: number;
  host_username: string;
  mode: GameMode;
  status: GameStatus;
  max_players: number;
  playlist_id?: string;
  is_online: boolean;
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
  mode: GameMode;
  max_players: number;
  playlist_id?: string;
  is_online: boolean;
}

export interface GameRound {
  id: number;
  game: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  options: string[];
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
