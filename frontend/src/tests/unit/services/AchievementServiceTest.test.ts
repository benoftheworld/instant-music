import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { achievementService } from '@/services/achievementService';
import { api } from '@/services/api';
import { createAchievement, createUserAchievement } from '@/tests/shared/factories';

class AchievementServiceTest extends BaseServiceTest {
  protected name = 'achievementService';

  run() {
    describe('achievementService', () => {
      this.setup(api);

      this.testGetAllArray();
      this.testGetAllPaginated();
      this.testGetMine();
      this.testGetByUser();
      this.testGetAllError();
    });
  }

  private testGetAllArray() {
    it('getAll — format array', async () => {
      const achievements = [createAchievement()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: achievements });
      const result = await achievementService.getAll();
      expect(result).toEqual(achievements);
    });
  }

  private testGetAllPaginated() {
    it('getAll — format paginé', async () => {
      const achievements = [createAchievement()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { results: achievements } });
      const result = await achievementService.getAll();
      expect(result).toEqual(achievements);
    });
  }

  private testGetMine() {
    it('getMine — succès', async () => {
      const items = [createUserAchievement()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: items });
      const result = await achievementService.getMine();
      expect(result).toEqual(items);
    });
  }

  private testGetByUser() {
    it('getByUser — succès', async () => {
      const items = [createUserAchievement()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: items });
      const result = await achievementService.getByUser('42');
      expect(result).toEqual(items);
      expect(api.get).toHaveBeenCalledWith('/achievements/user/42/');
    });
  }

  private testGetAllError() {
    it('getAll — erreur 500', async () => {
      this.mockError('get', 500, { detail: 'Erreur serveur' });
      await expect(achievementService.getAll()).rejects.toThrow();
    });
  }
}

new AchievementServiceTest().run();
