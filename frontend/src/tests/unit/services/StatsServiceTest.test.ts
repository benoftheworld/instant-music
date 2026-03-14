import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { statsService } from '@/services/statsService';
import { api } from '@/services/api';
import { createUserDetailedStats, createLeaderboardEntry, createTeamLeaderboardEntry, createUserPublicProfile } from '@/tests/shared/factories';

class StatsServiceTest extends BaseServiceTest {
  protected name = 'statsService';

  run() {
    describe('statsService', () => {
      this.setup(api);

      this.testGetMyStats();
      this.testGetLeaderboard();
      this.testGetLeaderboardByMode();
      this.testGetTeamLeaderboard();
      this.testGetMyRank();
      this.testGetUserStats();
      this.testGetUserStatsError();
    });
  }

  private testGetMyStats() {
    it('getMyStats — succès', async () => {
      const stats = createUserDetailedStats();
      this.mockGet('/stats/me/', stats);
      const result = await statsService.getMyStats();
      expect(result).toEqual(stats);
    });
  }

  private testGetLeaderboard() {
    it('getLeaderboard — succès', async () => {
      const response = { results: [createLeaderboardEntry()], count: 1, page: 1, page_size: 50 };
      this.mockGet('/stats/leaderboard/', response);
      const result = await statsService.getLeaderboard();
      expect(result.results).toHaveLength(1);
      expect(api.get).toHaveBeenCalledWith('/stats/leaderboard/', { params: { page: 1, page_size: 50 } });
    });
  }

  private testGetLeaderboardByMode() {
    it('getLeaderboardByMode — succès', async () => {
      const response = { results: [], count: 0, page: 1, page_size: 50 };
      this.mockGet('/stats/leaderboard/classique/', response);
      const result = await statsService.getLeaderboardByMode('classique');
      expect(result.results).toHaveLength(0);
    });
  }

  private testGetTeamLeaderboard() {
    it('getTeamLeaderboard — succès', async () => {
      const response = { results: [createTeamLeaderboardEntry()], count: 1, page: 1, page_size: 50 };
      this.mockGet('/stats/leaderboard/teams/', response);
      const result = await statsService.getTeamLeaderboard();
      expect(result.results).toHaveLength(1);
    });
  }

  private testGetMyRank() {
    it('getMyRank — succès', async () => {
      const rank = { general_rank: 5, total_players: 100, mode_ranks: {} };
      this.mockGet('/stats/my-rank/', rank);
      const result = await statsService.getMyRank();
      expect(result.general_rank).toBe(5);
    });
  }

  private testGetUserStats() {
    it('getUserStats — succès', async () => {
      const profile = createUserPublicProfile();
      this.mockGet('/stats/user/42/', profile);
      const result = await statsService.getUserStats('42');
      expect(result).toEqual(profile);
    });
  }

  private testGetUserStatsError() {
    it('getUserStats — erreur 404', async () => {
      this.mockError('get', 404, { detail: 'Utilisateur introuvable.' });
      await expect(statsService.getUserStats('999')).rejects.toThrow();
    });
  }
}

new StatsServiceTest().run();
