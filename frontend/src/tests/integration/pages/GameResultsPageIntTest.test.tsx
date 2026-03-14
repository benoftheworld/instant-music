import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import GameResultsPage from '@/pages/game/GameResultsPage';

vi.mock('@/hooks/pages/useGameResultsPage', () => ({
  useGameResultsPage: () => {
    const rankings = [
      { rank: 1, username: 'alice', user_id: 1, avatar: null, score: 300, correct_answers: 8, avg_response_time: 3.5, bonuses_used: 0 },
      { rank: 2, username: 'bob', user_id: 2, avatar: null, score: 250, correct_answers: 7, avg_response_time: 4.0, bonuses_used: 0 },
    ];
    const top3 = rankings.slice(0, 3);
    const others = rankings.slice(3);
    return {
      roomCode: 'ABC123',
      navigate: vi.fn(),
      loading: false,
      results: {
        game: { id: '1', room_code: 'ABC123', mode: 'classique', status: 'finished', host: 1, is_party_mode: false },
        rankings,
        rounds: [],
      },
      downloadingPdf: false,
      showFullRanking: false,
      setShowFullRanking: vi.fn(),
      handleDownloadPdf: vi.fn(),
      game: { id: '1', room_code: 'ABC123', mode: 'classique', status: 'finished', host: 1, is_party_mode: false },
      rankings,
      rounds: [],
      top3,
      others,
      winner: rankings[0] ?? null,
      podiumOrder: [top3[1] ?? null, top3[0] ?? null, top3[2] ?? null],
    };
  },
}));

class GameResultsPageIntTest extends BasePageTest {
  protected getRoute() { return '/game/:roomCode/results'; }
  protected getComponent() { return GameResultsPage; }

  run() {
    describe('GameResultsPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersRankings();
      this.testRendersPodium();
    });
  }

  private testRendersRankings() {
    it('affiche le classement des joueurs', () => {
      this.renderPage(['/game/ABC123/results']);
      expect(screen.getAllByText('alice').length).toBeGreaterThan(0);
      expect(screen.getAllByText('bob').length).toBeGreaterThan(0);
    });
  }

  private testRendersPodium() {
    it('affiche les médailles du podium', () => {
      this.renderPage(['/game/ABC123/results']);
      expect(screen.getAllByText('🥇').length).toBeGreaterThan(0);
      expect(screen.getAllByText('🥈').length).toBeGreaterThan(0);
    });
  }
}

new GameResultsPageIntTest().run();
