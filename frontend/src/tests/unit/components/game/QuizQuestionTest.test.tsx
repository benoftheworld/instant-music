import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

vi.mock('@/components/game/useAudioPlayer', () => ({
  useAudioPlayer: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
}));

import QuizQuestion from '@/components/game/QuizQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Opt1', 'Opt2', 'Opt3', 'Opt4'],
    question_type: 'quiz',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class QuizQuestionTest {
  run() {
    describe('QuizQuestion', () => {
      this.testRendersDefaultTitle();
      this.testRendersOptions();
    });
  }

  private testRendersDefaultTitle() {
    it('affiche le titre par défaut "Quel est le titre de ce morceau ?"', () => {
      render(
        <QuizQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Quel est le titre de ce morceau ?')).toBeInTheDocument();
    });
  }

  private testRendersOptions() {
    it('affiche les 4 options', () => {
      render(
        <QuizQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Opt1')).toBeInTheDocument();
      expect(screen.getByText('Opt4')).toBeInTheDocument();
    });
  }
}

new QuizQuestionTest().run();
