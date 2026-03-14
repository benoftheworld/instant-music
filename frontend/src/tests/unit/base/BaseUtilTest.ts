/**
 * Classe abstraite de base pour les tests de fonctions utilitaires.
 *
 * Factorise : tests de fonctions pures, tests de regex, tests d'edge cases.
 */
import { it, expect } from 'vitest';

export abstract class BaseUtilTest {
  protected abstract name: string;

  /**
   * Teste une fonction pure avec un tableau d'entrées/sorties attendues.
   */
  protected testPureFunction<TInput, TOutput>(
    description: string,
    fn: (input: TInput) => TOutput,
    cases: Array<{ input: TInput; expected: TOutput; label?: string }>,
  ) {
    for (const { input, expected, label } of cases) {
      const testLabel = label ?? `${description} — ${JSON.stringify(input)} → ${JSON.stringify(expected)}`;
      it(testLabel, () => {
        expect(fn(input)).toEqual(expected);
      });
    }
  }

  /**
   * Teste une regex avec des cas valides et invalides.
   */
  protected testRegex(
    description: string,
    regex: RegExp,
    validCases: string[],
    invalidCases: string[],
  ) {
    for (const value of validCases) {
      it(`${description} — accepte "${value}"`, () => {
        expect(regex.test(value)).toBe(true);
      });
    }
    for (const value of invalidCases) {
      it(`${description} — rejette "${value}"`, () => {
        expect(regex.test(value)).toBe(false);
      });
    }
  }

  /**
   * Teste une fonction avec des cas limites (edge cases).
   */
  protected testEdgeCases<TInput, TOutput>(
    description: string,
    fn: (input: TInput) => TOutput,
    cases: Array<{ input: TInput; expected: TOutput; label: string }>,
  ) {
    for (const { input, expected, label } of cases) {
      it(`${description} — edge case : ${label}`, () => {
        expect(fn(input)).toEqual(expected);
      });
    }
  }
}
