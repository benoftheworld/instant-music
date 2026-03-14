import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrackReveal } from '@/components/game/TrackReveal';
import type { GameRound } from '@/components/game/types';

class TrackRevealTest {
  private makeRound(overrides: Partial<GameRound> = {}): GameRound {
    return {
      round_number: 1,
      track_name: 'Bohemian Rhapsody',
      artist_name: 'Queen',
      preview_url: 'http://example.com/preview.mp3',
      duration: 30,
      options: [],
      question_type: 'quiz',
      question_text: '',
      extra_data: {},
      ...overrides,
    } as GameRound;
  }

  run() {
    describe('TrackReveal', () => {
      this.testRendersTrackName();
      this.testRendersArtistName();
    });
  }

  private testRendersTrackName() {
    it('affiche le nom du morceau', () => {
      render(<TrackReveal round={this.makeRound()} />);
      expect(screen.getByText(/Bohemian Rhapsody/)).toBeInTheDocument();
    });
  }

  private testRendersArtistName() {
    it("affiche le nom de l'artiste", () => {
      render(<TrackReveal round={this.makeRound()} />);
      expect(screen.getByText('Queen')).toBeInTheDocument();
    });
  }
}

new TrackRevealTest().run();
