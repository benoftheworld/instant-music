import { describe, it, expect } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { DEFAULT_PLAYLISTS, PLAYLIST_CATEGORIES } from '@/constants/defaultPlaylists';

class DefaultPlaylistsTest extends BaseUtilTest {
  protected name = 'defaultPlaylists constants';

  run() {
    describe('DEFAULT_PLAYLISTS', () => {
      this.testNotEmpty();
      this.testPlaylistFields();
      this.testUniqueIds();
      this.testCategoriesMatchConst();
    });

    describe('PLAYLIST_CATEGORIES', () => {
      this.testCategoriesNotEmpty();
      this.testFirstIsTous();
      this.testUnique();
    });
  }

  private testNotEmpty() {
    it('contient des playlists', () => {
      expect(DEFAULT_PLAYLISTS.length).toBeGreaterThan(0);
    });
  }

  private testPlaylistFields() {
    it('chaque playlist a les champs requis', () => {
      for (const playlist of DEFAULT_PLAYLISTS) {
        expect(playlist.youtube_id).toBeTruthy();
        expect(playlist.name).toBeTruthy();
        expect(playlist.description).toBeTruthy();
        expect(playlist.owner).toBeTruthy();
        expect(playlist.category).toBeTruthy();
      }
    });
  }

  private testUniqueIds() {
    it('chaque playlist a un ID unique', () => {
      const ids = DEFAULT_PLAYLISTS.map((p) => p.youtube_id);
      expect(new Set(ids).size).toBe(ids.length);
    });
  }

  private testCategoriesMatchConst() {
    it('chaque catégorie de playlist existe dans PLAYLIST_CATEGORIES', () => {
      const categories = new Set(PLAYLIST_CATEGORIES);
      for (const playlist of DEFAULT_PLAYLISTS) {
        expect(categories.has(playlist.category)).toBe(true);
      }
    });
  }

  private testCategoriesNotEmpty() {
    it('contient des catégories', () => {
      expect(PLAYLIST_CATEGORIES.length).toBeGreaterThan(0);
    });
  }

  private testFirstIsTous() {
    it('la première catégorie est "Tous"', () => {
      expect(PLAYLIST_CATEGORIES[0]).toBe('Tous');
    });
  }

  private testUnique() {
    it('chaque catégorie est unique', () => {
      expect(new Set(PLAYLIST_CATEGORIES).size).toBe(PLAYLIST_CATEGORIES.length);
    });
  }
}

new DefaultPlaylistsTest().run();
