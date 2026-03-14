import { describe, it, expect } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { BONUS_META, getBonusMeta } from '@/constants/bonuses';
import type { BonusType } from '@/types';

const ALL_BONUS_TYPES: BonusType[] = [
  'double_points', 'max_points', 'time_bonus', 'fifty_fifty',
  'steal', 'shield', 'fog', 'joker',
];

class BonusesTest extends BaseUtilTest {
  protected name = 'bonuses constants';

  run() {
    describe('BONUS_META', () => {
      this.testAllTypesPresent();
      this.testMetaFields();
      this.testGetBonusMeta();
    });
  }

  private testAllTypesPresent() {
    it('contient tous les types de bonus', () => {
      for (const type of ALL_BONUS_TYPES) {
        expect(BONUS_META[type]).toBeDefined();
      }
    });
  }

  private testMetaFields() {
    for (const type of ALL_BONUS_TYPES) {
      it(`${type} a tous les champs requis`, () => {
        const meta = BONUS_META[type];
        expect(meta.emoji).toBeDefined();
        expect(meta.label).toBeTruthy();
        expect(meta.shortLabel).toBeTruthy();
        expect(meta.color).toBeTruthy();
        expect(meta.gradientClass).toBeTruthy();
        expect(meta.description).toBeTruthy();
      });
    }
  }

  private testGetBonusMeta() {
    it('getBonusMeta retourne les bonnes métadonnées', () => {
      const meta = getBonusMeta('double_points');
      expect(meta).toBe(BONUS_META.double_points);
      expect(meta.label).toBe('Points Doublés');
    });
  }
}

new BonusesTest().run();
