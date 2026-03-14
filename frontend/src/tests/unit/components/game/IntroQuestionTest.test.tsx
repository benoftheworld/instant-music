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

import IntroQuestion from '@/components/game/IntroQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Option Alpha', 'Option Beta', 'Option Gamma', 'Option Delta'],
    question_type: 'intro',
    question_text: '',
    extra_data: { audio_duration: 5 },
    ...overrides,
  } as GameRound;
}

class IntroQuestionTest {
  run() {
    describe('IntroQuestion', () => {
      this.testRendersIntroLabel();
      this.testRendersOptions();
    });
  }

  private testRendersIntroLabel() {
    it("affiche l'indication de durée d'écoute", () => {
      render(
        <IntroQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText(/5 secondes/)).toBeInTheDocument();
    });
  }

  private testRendersOptions() {
    it('affiche les 4 options', () => {
      render(
        <IntroQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Option Alpha')).toBeInTheDocument();
      expect(screen.getByText('Option Delta')).toBeInTheDocument();
    });
  }
}

new IntroQuestionTest().run();
