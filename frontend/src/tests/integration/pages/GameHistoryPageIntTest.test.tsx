import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import GameHistoryPage from '@/pages/GameHistoryPage';

vi.mock('@/hooks/pages/useGameHistoryPage', () => ({
  useGameHistoryPage: () => ({
    games: [
      {
        id: '1', room_code: 'ABC123', host_username: 'alice',
        mode: 'classique', mode_display: 'Classique',
        answer_mode: 'qcm', answer_mode_display: 'QCM',
        guess_target: 'artist', guess_target_display: 'Artiste',
        num_rounds: 5, playlist_id: null,
        winner: { id: 1, username: 'alice', avatar: null }, winner_score: 100,
        player_count: 3, participants: [],
        created_at: '2024-01-01T12:00:00Z', started_at: '2024-01-01T12:00:00Z', finished_at: '2024-01-01T12:30:00Z',
      },
      {
        id: '2', room_code: 'DEF456', host_username: 'bob',
        mode: 'rapide', mode_display: 'Rapide',
        answer_mode: 'free', answer_mode_display: 'Saisie libre',
        guess_target: 'title', guess_target_display: 'Titre',
        num_rounds: 3, playlist_id: null,
        winner: { id: 2, username: 'bob', avatar: null }, winner_score: 80,
        player_count: 2, participants: [],
        created_at: '2024-01-02T12:00:00Z', started_at: '2024-01-02T12:00:00Z', finished_at: '2024-01-02T12:15:00Z',
      },
    ],
    selectedMode: null,
    setSelectedMode: vi.fn(),
    loading: false,
    error: null,
    page: 1,
    pageSize: 20,
    totalCount: 2,
    hasNext: false,
    hasPrev: false,
    handlePrev: vi.fn(),
    handleNext: vi.fn(),
    formatDate: (d: string) => '01/01/2024',
  }),
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string) => url ?? '',
}));

class GameHistoryPageIntTest extends BasePageTest {
  protected getRoute() { return '/game/history'; }
  protected getComponent() { return GameHistoryPage; }

  run() {
    describe('GameHistoryPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTitle();
      this.testRendersGames();
      this.testRendersModeFilter();
    });
  }

  private testRendersTitle() {
    it('affiche le titre', () => {
      this.renderPage();
      expect(screen.getByText('Historique des parties')).toBeInTheDocument();
    });
  }

  private testRendersGames() {
    it('affiche les parties', () => {
      this.renderPage();
      expect(screen.getAllByText(/ABC123/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/DEF456/).length).toBeGreaterThan(0);
    });
  }

  private testRendersModeFilter() {
    it('affiche le filtre par mode', () => {
      this.renderPage();
      expect(screen.getByText('Tous')).toBeInTheDocument();
    });
  }
}

new GameHistoryPageIntTest().run();
