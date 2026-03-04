import { api } from './api';
import type { UserDetailedStats, MyRank, GameMode } from '@/types';

/** Réponse paginée du leaderboard. */
export interface LeaderboardResponse {
  results: LeaderboardEntry[];
  count: number;
  page: number;
  page_size: number;
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  avatar?: string;
  score: number;
  games_played: number;
  [key: string]: unknown;
}

export const statsService = {
  /** Get detailed stats for the current user */
  async getMyStats(): Promise<UserDetailedStats> {
    const response = await api.get<UserDetailedStats>('/stats/me/');
    return response.data;
  },

  /** Get general leaderboard */
  async getLeaderboard(page = 1, page_size = 50): Promise<LeaderboardResponse> {
    const response = await api.get<LeaderboardResponse>('/stats/leaderboard/', {
      params: { page, page_size },
    });
    return response.data;
  },

  /** Get leaderboard by game mode */
  async getLeaderboardByMode(mode: GameMode, page = 1, page_size = 50): Promise<LeaderboardResponse> {
    const response = await api.get<LeaderboardResponse>(`/stats/leaderboard/${mode}/`, {
      params: { page, page_size },
    });
    return response.data;
  },

  /** Get team leaderboard */
  async getTeamLeaderboard(page = 1, page_size = 50): Promise<LeaderboardResponse> {
    const response = await api.get<LeaderboardResponse>('/stats/leaderboard/teams/', {
      params: { page, page_size },
    });
    return response.data;
  },

  /** Get current user's rank in leaderboards */
  async getMyRank(): Promise<MyRank> {
    const response = await api.get<MyRank>('/stats/my-rank/');
    return response.data;
  },
};
