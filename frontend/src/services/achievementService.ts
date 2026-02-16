import { api } from './api';
import type { Achievement, UserAchievement, UserDetailedStats, LeaderboardEntry, TeamLeaderboardEntry, MyRank, GameMode } from '@/types';

export const achievementService = {
  /** Get all achievements with unlock status for current user */
  async getAll(): Promise<Achievement[]> {
    const response = await api.get<Achievement[] | { results: Achievement[] }>('/achievements/');
    const data = response.data;
    return Array.isArray(data) ? data : data.results ?? [];
  },

  /** Get achievements unlocked by the current user */
  async getMine(): Promise<UserAchievement[]> {
    const response = await api.get<UserAchievement[]>('/achievements/mine/');
    return response.data;
  },

  /** Get achievements unlocked by a specific user */
  async getByUser(userId: number): Promise<UserAchievement[]> {
    const response = await api.get<UserAchievement[]>(`/achievements/user/${userId}/`);
    return response.data;
  },
};

export const statsService = {
  /** Get detailed stats for the current user */
  async getMyStats(): Promise<UserDetailedStats> {
    const response = await api.get<UserDetailedStats>('/stats/me/');
    return response.data;
  },

  /** Get general leaderboard */
  async getLeaderboard(limit = 50): Promise<LeaderboardEntry[]> {
    const response = await api.get<LeaderboardEntry[]>('/stats/leaderboard/', {
      params: { limit },
    });
    return response.data;
  },

  /** Get leaderboard by game mode */
  async getLeaderboardByMode(mode: GameMode, limit = 50): Promise<LeaderboardEntry[]> {
    const response = await api.get<LeaderboardEntry[]>(`/stats/leaderboard/${mode}/`, {
      params: { limit },
    });
    return response.data;
  },

  /** Get team leaderboard */
  async getTeamLeaderboard(limit = 50): Promise<TeamLeaderboardEntry[]> {
    const response = await api.get<TeamLeaderboardEntry[]>('/stats/leaderboard/teams/', {
      params: { limit },
    });
    return response.data;
  },

  /** Get current user's rank in leaderboards */
  async getMyRank(): Promise<MyRank> {
    const response = await api.get<MyRank>('/stats/my-rank/');
    return response.data;
  },
};
