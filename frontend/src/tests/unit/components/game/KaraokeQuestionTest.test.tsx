import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

// Mock YouTube IFrame API — KaraokeQuestion loads it dynamically
vi.stubGlobal('YT', { Player: vi.fn() });

import KaraokeQuestion from '@/components/game/KaraokeQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Imagine',
    artist_name: 'John Lennon',
    preview_url: '',
    duration: 30,
    options: [],
    question_type: 'karaoke',
    question_text: '',
    extra_data: {
      youtube_video_id: 'dQw4w9WgXcQ',
      synced_lyrics: [
        { time_ms: 0, text: 'Imagine all the people' },
        { time_ms: 5000, text: 'living for today' },
      ],
    },
    ...overrides,
  } as GameRound;
}

class KaraokeQuestionTest {
  run() {
    describe('KaraokeQuestion', () => {
      this.testRendersTrackInfoDuringPlay();
      this.testShowsResultsPhase();
    });
  }

  private testRendersTrackInfoDuringPlay() {
    it("affiche le titre et l'artiste pendant la lecture", () => {
      render(
        <KaraokeQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Imagine')).toBeInTheDocument();
      expect(screen.getByText('John Lennon')).toBeInTheDocument();
    });
  }

  private testShowsResultsPhase() {
    it("affiche la phase résultats avec titre et artiste", () => {
      render(
        <KaraokeQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={true}
          roundResults={{ correct_answer: 'Imagine', points_earned: 0 }}
        />,
      );
      expect(screen.getByText('Imagine')).toBeInTheDocument();
      expect(screen.getByText('John Lennon')).toBeInTheDocument();
    });
  }
}

new KaraokeQuestionTest().run();
