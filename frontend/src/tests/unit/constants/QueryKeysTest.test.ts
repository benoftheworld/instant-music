import { describe, it, expect } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { QUERY_KEYS } from '@/constants/queryKeys';

class QueryKeysTest extends BaseUtilTest {
  protected name = 'queryKeys constants';

  run() {
    describe('QUERY_KEYS', () => {
      this.testKeysAreFunctions();
      this.testKeysReturnArrays();
      this.testUniqueKeys();
      this.testLeaderboardKeyWithParams();
    });
  }

  private testKeysAreFunctions() {
    it('toutes les clés sont des fonctions', () => {
      for (const [key, value] of Object.entries(QUERY_KEYS)) {
        expect(typeof value).toBe('function');
      }
    });
  }

  private testKeysReturnArrays() {
    it('chaque clé retourne un tableau', () => {
      expect(Array.isArray(QUERY_KEYS.topPlayers())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.recentGames())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.siteStatus())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.friends())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.shop())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.shopItems())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.shopSummary())).toBe(true);
      expect(Array.isArray(QUERY_KEYS.shopInventory())).toBe(true);
    });
  }

  private testUniqueKeys() {
    it('chaque clé simple est unique', () => {
      const keys = [
        QUERY_KEYS.topPlayers(),
        QUERY_KEYS.recentGames(),
        QUERY_KEYS.siteStatus(),
        QUERY_KEYS.friends(),
        QUERY_KEYS.teamsAll(),
        QUERY_KEYS.profileAchievements(),
        QUERY_KEYS.profileStats(),
        QUERY_KEYS.shop(),
      ];
      const asStrings = keys.map((k) => JSON.stringify(k));
      expect(new Set(asStrings).size).toBe(asStrings.length);
    });
  }

  private testLeaderboardKeyWithParams() {
    it('leaderboard key inclut mode, page et page_size', () => {
      const key = QUERY_KEYS.leaderboard('classique', 2, 25);
      expect(key).toEqual(['leaderboard', 'classique', 2, 25]);
    });
  }
}

new QueryKeysTest().run();
