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

import SlowQuestion from '@/components/game/SlowQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['A', 'B', 'C', 'D'],
    question_type: 'slow',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class SlowQuestionTest {
  run() {
    describe('SlowQuestion', () => {
      this.testRendersSlowSubtitle();
    });
  }

  private testRendersSlowSubtitle() {
    it('affiche le sous-titre ralenti', () => {
      render(
        <SlowQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText(/ralenti/)).toBeInTheDocument();
    });
  }
}

new SlowQuestionTest().run();
