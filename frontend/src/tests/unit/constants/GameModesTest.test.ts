import { describe, it, expect } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { GAME_MODE_CONFIG, LEADERBOARD_TABS, getModeIcon, getModeLabel } from '@/constants/gameModes';
import type { GameMode } from '@/types';

const ALL_MODES: GameMode[] = ['classique', 'rapide', 'generation', 'paroles', 'karaoke', 'mollo'];

class GameModesTest extends BaseUtilTest {
  protected name = 'gameModes constants';

  run() {
    describe('GAME_MODE_CONFIG', () => {
      this.testAllModesPresent();
      this.testConfigFields();
    });

    describe('LEADERBOARD_TABS', () => {
      this.testTabsIncludeGeneral();
      this.testTabsIncludeTeams();
      this.testTabsIncludeAllModes();
    });

    describe('getModeIcon', () => {
      this.testGetModeIcon();
      this.testGetModeIconUnknown();
    });

    describe('getModeLabel', () => {
      this.testGetModeLabel();
      this.testGetModeLabelUnknown();
    });
  }

  private testAllModesPresent() {
    it('contient tous les modes de jeu', () => {
      for (const mode of ALL_MODES) {
        expect(GAME_MODE_CONFIG[mode]).toBeDefined();
      }
    });
  }

  private testConfigFields() {
    for (const mode of ALL_MODES) {
      it(`${mode} a label, icon et description`, () => {
        const config = GAME_MODE_CONFIG[mode];
        expect(config.label).toBeTruthy();
        expect(config.icon).toBeTruthy();
        expect(config.description).toBeTruthy();
      });
    }
  }

  private testTabsIncludeGeneral() {
    it('inclut l\'onglet général', () => {
      expect(LEADERBOARD_TABS.find((t) => t.value === 'general')).toBeDefined();
    });
  }

  private testTabsIncludeTeams() {
    it('inclut l\'onglet équipes', () => {
      expect(LEADERBOARD_TABS.find((t) => t.value === 'teams')).toBeDefined();
    });
  }

  private testTabsIncludeAllModes() {
    it('inclut tous les modes de jeu', () => {
      for (const mode of ALL_MODES) {
        expect(LEADERBOARD_TABS.find((t) => t.value === mode)).toBeDefined();
      }
    });
  }

  private testGetModeIcon() {
    this.testPureFunction('retourne la bonne icône', getModeIcon, [
      { input: 'classique', expected: '🎵' },
      { input: 'rapide', expected: '⚡' },
      { input: 'karaoke', expected: '🎤' },
    ]);
  }

  private testGetModeIconUnknown() {
    this.testPureFunction('retourne 🎮 pour un mode inconnu', getModeIcon, [
      { input: 'unknown_mode', expected: '🎮' },
    ]);
  }

  private testGetModeLabel() {
    this.testPureFunction('retourne le bon label', getModeLabel, [
      { input: 'classique', expected: 'Classique' },
      { input: 'rapide', expected: 'Rapide' },
    ]);
  }

  private testGetModeLabelUnknown() {
    this.testPureFunction('retourne le mode brut pour un mode inconnu', getModeLabel, [
      { input: 'unknown_mode', expected: 'unknown_mode' },
    ]);
  }
}

new GameModesTest().run();
