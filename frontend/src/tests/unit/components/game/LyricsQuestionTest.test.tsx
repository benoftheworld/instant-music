import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

vi.mock('@/components/game/useAudioPlayer', () => ({
  useAudioPlayerOnResults: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
}));

import LyricsQuestion from '@/components/game/LyricsQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Word1', 'Word2', 'Word3', 'Word4'],
    question_type: 'lyrics',
    question_text: 'Complétez les paroles',
    extra_data: { lyrics_snippet: 'Hello _____ my old friend' },
    ...overrides,
  } as GameRound;
}

class LyricsQuestionTest {
  run() {
    describe('LyricsQuestion', () => {
      this.testRendersTitle();
      this.testRendersSnippet();
      this.testRendersOptions();
    });
  }

  private testRendersTitle() {
    it('affiche le titre "Complétez les paroles"', () => {
      render(
        <LyricsQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Complétez les paroles')).toBeInTheDocument();
    });
  }

  private testRendersSnippet() {
    it('affiche le snippet avec le trou', () => {
      render(
        <LyricsQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('???')).toBeInTheDocument();
    });
  }

  private testRendersOptions() {
    it('affiche les 4 options', () => {
      render(
        <LyricsQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Word1')).toBeInTheDocument();
      expect(screen.getByText('Word4')).toBeInTheDocument();
    });
  }
}

new LyricsQuestionTest().run();
