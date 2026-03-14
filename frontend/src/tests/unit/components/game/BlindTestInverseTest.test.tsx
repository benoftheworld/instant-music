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

import BlindTestInverse from '@/components/game/BlindTestInverse';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'The Beatles',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Song A', 'Song B', 'Song C', 'Song D'],
    question_type: 'blind_inverse',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class BlindTestInverseTest {
  run() {
    describe('BlindTestInverse', () => {
      this.testRendersArtistSubtitle();
      this.testRendersOptions();
    });
  }

  private testRendersArtistSubtitle() {
    it("affiche l'artiste en sous-titre", () => {
      render(
        <BlindTestInverse
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('The Beatles')).toBeInTheDocument();
    });
  }

  private testRendersOptions() {
    it('affiche les options', () => {
      render(
        <BlindTestInverse
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Song A')).toBeInTheDocument();
      expect(screen.getByText('Song D')).toBeInTheDocument();
    });
  }
}

new BlindTestInverseTest().run();
