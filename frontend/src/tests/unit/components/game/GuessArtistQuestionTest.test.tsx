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

import GuessArtistQuestion from '@/components/game/GuessArtistQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Artist A', 'Artist B', 'Artist C', 'Artist D'],
    question_type: 'guess_artist',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class GuessArtistQuestionTest {
  run() {
    describe('GuessArtistQuestion', () => {
      this.testRendersTitle();
      this.testRendersOptions();
    });
  }

  private testRendersTitle() {
    it('affiche "Qui interprète ce morceau ?"', () => {
      render(
        <GuessArtistQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Qui interprète ce morceau ?')).toBeInTheDocument();
    });
  }

  private testRendersOptions() {
    it('affiche les options', () => {
      render(
        <GuessArtistQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Artist A')).toBeInTheDocument();
    });
  }
}

new GuessArtistQuestionTest().run();
