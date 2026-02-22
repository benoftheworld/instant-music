import { api } from './api';
import type { Achievement, UserAchievement, UserDetailedStats, MyRank, GameMode } from '@/types';

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
  async getLeaderboard(page = 1, page_size = 50): Promise<any> {
    const response = await api.get('/stats/leaderboard/', {
      params: { page, page_size },
    });
    return response.data;
  },

  /** Get leaderboard by game mode */
  async getLeaderboardByMode(mode: GameMode, page = 1, page_size = 50): Promise<any> {
    const response = await api.get(`/stats/leaderboard/${mode}/`, {
      params: { page, page_size },
    });
    return response.data;
  },

  /** Get team leaderboard */
  async getTeamLeaderboard(page = 1, page_size = 50): Promise<any> {
    const response = await api.get('/stats/leaderboard/teams/', {
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
