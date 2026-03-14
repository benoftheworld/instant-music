import { describe, it, expect } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { mergeUpdatedPlayers } from '@/utils/mergeUpdatedPlayers';
import { createGamePlayer } from '@/tests/shared/factories';

class MergeUpdatedPlayersTest extends BaseUtilTest {
  protected name = 'mergeUpdatedPlayers';

  run() {
    describe('mergeUpdatedPlayers', () => {
      this.testMergesScores();
      this.testPreservesUnupdated();
      this.testPreservesAvatar();
      this.testOverwritesAvatarWhenFlagOff();
      this.testEmptyUpdates();
      this.testEmptyExisting();
    });
  }

  private testMergesScores() {
    it('met à jour les scores des joueurs existants', () => {
      const existing = [
        createGamePlayer({ id: 1, username: 'alice', score: 100 }),
        createGamePlayer({ id: 2, username: 'bob', score: 200 }),
      ];
      const updated = [{ id: 1, score: 300 }];
      const result = mergeUpdatedPlayers(existing, updated);
      expect(result[0].score).toBe(300);
      expect(result[1].score).toBe(200);
    });
  }

  private testPreservesUnupdated() {
    it('conserve les joueurs sans mise à jour', () => {
      const existing = [
        createGamePlayer({ id: 1, username: 'alice', score: 100 }),
        createGamePlayer({ id: 2, username: 'bob', score: 200 }),
      ];
      const result = mergeUpdatedPlayers(existing, [{ id: 1, score: 999 }]);
      expect(result[1]).toEqual(existing[1]);
    });
  }

  private testPreservesAvatar() {
    it('conserve l\'avatar existant si le nouveau est absent (preserveAvatar=true)', () => {
      const existing = [createGamePlayer({ id: 1, avatar: 'old.png' })];
      const updated = [{ id: 1, score: 999 }];
      const result = mergeUpdatedPlayers(existing, updated, true);
      expect(result[0].avatar).toBe('old.png');
    });
  }

  private testOverwritesAvatarWhenFlagOff() {
    it('écrase l\'avatar si preserveAvatar=false', () => {
      const existing = [createGamePlayer({ id: 1, avatar: 'old.png' })];
      const updated = [{ id: 1, avatar: undefined }];
      const result = mergeUpdatedPlayers(existing, updated, false);
      expect(result[0].avatar).toBeUndefined();
    });
  }

  private testEmptyUpdates() {
    it('retourne la liste originale si aucune mise à jour', () => {
      const existing = [createGamePlayer({ id: 1 })];
      const result = mergeUpdatedPlayers(existing, []);
      expect(result).toEqual(existing);
    });
  }

  private testEmptyExisting() {
    it('retourne une liste vide si aucun joueur existant', () => {
      const result = mergeUpdatedPlayers([], [{ id: 1, score: 100 }]);
      expect(result).toEqual([]);
    });
  }
}

new MergeUpdatedPlayersTest().run();
