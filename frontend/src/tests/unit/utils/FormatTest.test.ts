import { describe } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { formatDate, formatFullDate, formatDuration, formatTime, formatLocalDate } from '@/utils/format';

class FormatTest extends BaseUtilTest {
  protected name = 'format utils';

  run() {
    describe('formatDate', () => {
      this.testFormatDateNull();
      this.testFormatDateJustNow();
      this.testFormatDateMinutes();
      this.testFormatDateHours();
      this.testFormatDateDays();
      this.testFormatDateOld();
    });

    describe('formatFullDate', () => {
      this.testFormatFullDateNull();
      this.testFormatFullDate();
    });

    describe('formatDuration', () => {
      this.testFormatDuration();
    });

    describe('formatTime', () => {
      this.testFormatTime();
    });

    describe('formatLocalDate', () => {
      this.testFormatLocalDate();
    });
  }

  private testFormatDateNull() {
    this.testPureFunction('retourne N/A pour null', (v: string | null) => formatDate(v), [
      { input: null, expected: 'N/A' },
    ]);
  }

  private testFormatDateJustNow() {
    this.testPureFunction(
      'retourne "À l\'instant" pour une date récente',
      () => formatDate(new Date().toISOString()),
      [{ input: undefined as any, expected: "À l'instant", label: 'just now' }],
    );
  }

  private testFormatDateMinutes() {
    const fiveMinAgo = new Date(Date.now() - 5 * 60_000).toISOString();
    this.testPureFunction(
      'retourne "Il y a X min"',
      () => formatDate(fiveMinAgo),
      [{ input: undefined as any, expected: 'Il y a 5 min', label: '5 min ago' }],
    );
  }

  private testFormatDateHours() {
    const threeHoursAgo = new Date(Date.now() - 3 * 3_600_000).toISOString();
    this.testPureFunction(
      'retourne "Il y a Xh"',
      () => formatDate(threeHoursAgo),
      [{ input: undefined as any, expected: 'Il y a 3h', label: '3h ago' }],
    );
  }

  private testFormatDateDays() {
    const twoDaysAgo = new Date(Date.now() - 2 * 86_400_000).toISOString();
    this.testPureFunction(
      'retourne "Il y a Xj"',
      () => formatDate(twoDaysAgo),
      [{ input: undefined as any, expected: 'Il y a 2j', label: '2 days ago' }],
    );
  }

  private testFormatDateOld() {
    const oldDate = '2024-03-12T10:00:00.000Z';
    this.testPureFunction(
      'retourne une date format DD/MM pour dates anciennes',
      () => {
        const result = formatDate(oldDate);
        // Should be DD/MM format
        return /^\d{2}\/\d{2}$/.test(result);
      },
      [{ input: undefined as any, expected: true, label: 'old date DD/MM format' }],
    );
  }

  private testFormatFullDateNull() {
    this.testPureFunction('retourne N/A pour null', (v: string | null) => formatFullDate(v), [
      { input: null, expected: 'N/A' },
    ]);
  }

  private testFormatFullDate() {
    this.testPureFunction(
      'retourne une date complète',
      () => {
        const result = formatFullDate('2024-03-12T14:30:00.000Z');
        // Should contain DD/MM/YYYY HH:MM
        return result.includes('2024') && result.includes('12');
      },
      [{ input: undefined as any, expected: true, label: 'full date contains year' }],
    );
  }

  private testFormatDuration() {
    this.testPureFunction(
      'formate des millisecondes en MM:SS',
      (ms: number) => formatDuration(ms),
      [
        { input: 0, expected: '--:--', label: '0 → --:--' },
        { input: 183000, expected: '3:03', label: '183000 → 3:03' },
        { input: 60000, expected: '1:00', label: '60000 → 1:00' },
        { input: 5000, expected: '0:05', label: '5000 → 0:05' },
      ],
    );
  }

  private testFormatTime() {
    this.testPureFunction(
      'formate des secondes en MM:SS',
      (s: number) => formatTime(s),
      [
        { input: 0, expected: '0:00', label: '0 → 0:00' },
        { input: 183, expected: '3:03', label: '183 → 3:03' },
        { input: 60, expected: '1:00', label: '60 → 1:00' },
        { input: 5, expected: '0:05', label: '5 → 0:05' },
        { input: 3661, expected: '61:01', label: '3661 → 61:01' },
      ],
    );
  }

  private testFormatLocalDate() {
    this.testPureFunction(
      'formate avec les options Intl',
      () => {
        const result = formatLocalDate('2024-03-12T14:30:00.000Z');
        return typeof result === 'string' && result.length > 0;
      },
      [{ input: undefined as any, expected: true, label: 'returns non-empty string' }],
    );
  }
}

new FormatTest().run();
