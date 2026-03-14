import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

vi.mock('@/components/game/useAudioPlayer', () => ({
  useAudioPlayer: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
}));

import YearQuestion from '@/components/game/YearQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['2000', '2005', '2010', '2015'],
    question_type: 'guess_year',
    question_text: '',
    extra_data: { year: '2010' },
    ...overrides,
  } as GameRound;
}

class YearQuestionTest {
  run() {
    describe('YearQuestion', () => {
      this.testRendersMcqOptions();
      this.testRendersTextModeInput();
      this.testTextModeSubmit();
    });
  }

  private testRendersMcqOptions() {
    it('affiche les options en mode QCM', () => {
      render(
        <YearQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('2000')).toBeInTheDocument();
      expect(screen.getByText('2015')).toBeInTheDocument();
    });
  }

  private testRendersTextModeInput() {
    it("affiche l'input numérique sans options", () => {
      render(
        <YearQuestion
          round={makeRound({ options: [] })}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByPlaceholderText('Ex: 2015')).toBeInTheDocument();
      expect(screen.getByText('Valider')).toBeInTheDocument();
    });
  }

  private testTextModeSubmit() {
    it('soumet la valeur saisie en mode texte', () => {
      const onSubmit = vi.fn();
      render(
        <YearQuestion
          round={makeRound({ options: [] })}
          onAnswerSubmit={onSubmit}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      fireEvent.change(screen.getByPlaceholderText('Ex: 2015'), { target: { value: '2010' } });
      fireEvent.click(screen.getByText('Valider'));
      expect(onSubmit).toHaveBeenCalledWith('2010');
    });
  }
}

new YearQuestionTest().run();
