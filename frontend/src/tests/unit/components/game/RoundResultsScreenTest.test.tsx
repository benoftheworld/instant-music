import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/utils/formatAnswer', () => ({
  formatAnswer: (a: string) => a,
}));

vi.mock('@/components/game/shared', () => ({
  useAudioPlayerOnResults: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
}));

vi.mock('@/constants/bonuses', () => ({
  BONUS_META: {
    fifty_fifty: { label: '50/50', emoji: '✂️' },
    steal: { label: 'Vol', emoji: '🦊' },
  },
}));

vi.mock('@/components/ui', () => ({
  Avatar: ({ username }: { username: string }) => <span data-testid="avatar">{username}</span>,
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

import RoundResultsScreen from '@/components/game/RoundResultsScreen';

function makeRound(overrides = {}) {
  return {
    round_number: 2,
    track_name: 'Bohemian Rhapsody',
    artist_name: 'Queen',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: [],
    question_type: 'quiz',
    question_text: '',
    extra_data: { year: '1975' },
    ...overrides,
  } as any;
}

function makePlayers() {
  return [
    { id: 1, username: 'alice', score: 200, avatar: null },
    { id: 2, username: 'bob', score: 150, avatar: null },
    { id: 3, username: 'charlie', score: 100, avatar: null },
  ] as any[];
}

class RoundResultsScreenTest {
  run() {
    describe('RoundResultsScreen', () => {
      this.testRendersRoundHeader();
      this.testRendersTrackInfo();
      this.testRendersTopPlayers();
      this.testContinueButton();
      this.testShowsPointsEarned();
    });
  }

  private testRendersRoundHeader() {
    it('affiche le numéro du round', () => {
      render(
        <RoundResultsScreen
          round={makeRound()}
          players={makePlayers()}
          correctAnswer="Bohemian Rhapsody"
          myPointsEarned={100}
        />,
      );
      expect(screen.getByText(/Fin du Round 2/)).toBeInTheDocument();
    });
  }

  private testRendersTrackInfo() {
    it('affiche le titre et artiste', () => {
      render(
        <RoundResultsScreen
          round={makeRound()}
          players={makePlayers()}
          correctAnswer="Bohemian Rhapsody"
          myPointsEarned={0}
        />,
      );
      expect(screen.getAllByText('Bohemian Rhapsody').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Queen').length).toBeGreaterThan(0);
    });
  }

  private testRendersTopPlayers() {
    it('affiche le classement des joueurs', () => {
      render(
        <RoundResultsScreen
          round={makeRound()}
          players={makePlayers()}
          correctAnswer="Bohemian Rhapsody"
          myPointsEarned={0}
        />,
      );
      expect(screen.getAllByText('alice').length).toBeGreaterThan(0);
      expect(screen.getAllByText('bob').length).toBeGreaterThan(0);
      expect(screen.getAllByText('charlie').length).toBeGreaterThan(0);
      expect(screen.getByText('🥇')).toBeInTheDocument();
    });
  }

  private testContinueButton() {
    it('affiche le bouton Continuer si callback fourni', () => {
      const onContinue = vi.fn();
      render(
        <RoundResultsScreen
          round={makeRound()}
          players={makePlayers()}
          correctAnswer="Bohemian Rhapsody"
          myPointsEarned={0}
          onContinue={onContinue}
        />,
      );
      fireEvent.click(screen.getByText('Continuer'));
      expect(onContinue).toHaveBeenCalled();
    });
  }

  private testShowsPointsEarned() {
    it('affiche les points gagnés', () => {
      render(
        <RoundResultsScreen
          round={makeRound()}
          players={makePlayers()}
          correctAnswer="Bohemian Rhapsody"
          myPointsEarned={150}
        />,
      );
      expect(screen.getByText(/\+150 points/)).toBeInTheDocument();
    });
  }
}

new RoundResultsScreenTest().run();
