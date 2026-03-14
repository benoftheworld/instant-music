import { describe, it, expect } from 'vitest';
import { getPasswordStrength } from '@/hooks/pages/useProfilePage';

class GetPasswordStrengthTest {
  run() {
    describe('getPasswordStrength', () => {
      this.testEmpty();
      this.testWeak();
      this.testMedium();
      this.testStrong();
    });
  }

  private testEmpty() {
    it('vide → score 0, label vide', () => {
      const result = getPasswordStrength('');
      expect(result.score).toBe(0);
      expect(result.label).toBe('');
    });
  }

  private testWeak() {
    it('court < 8 → Faible', () => {
      const result = getPasswordStrength('abc');
      expect(result.score).toBeLessThanOrEqual(1);
      expect(result.label).toBe('Faible');
      expect(result.colorClass).toBe('bg-red-500');
    });
  }

  private testMedium() {
    it('8+ avec majuscule → Moyen', () => {
      const result = getPasswordStrength('Abcdefgh');
      // length >= 8 (1) + uppercase (1) = 2
      expect(result.score).toBeGreaterThanOrEqual(2);
      expect(result.score).toBeLessThanOrEqual(3);
      expect(result.label).toBe('Moyen');
      expect(result.colorClass).toBe('bg-yellow-500');
    });
  }

  private testStrong() {
    it('12+ avec majuscule, chiffre, spécial → Fort', () => {
      const result = getPasswordStrength('Abcdefgh123!');
      // length >=8 (1), >=12 (1), uppercase (1), digit (1), special (1) = 5
      expect(result.score).toBeGreaterThanOrEqual(4);
      expect(result.label).toBe('Fort');
      expect(result.colorClass).toBe('bg-green-500');
    });
  }
}

new GetPasswordStrengthTest().run();
