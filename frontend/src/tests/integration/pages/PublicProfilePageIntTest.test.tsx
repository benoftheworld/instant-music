import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import PublicProfilePage from '@/pages/PublicProfilePage';

vi.mock('@/hooks/pages/usePublicProfilePage', () => ({
  usePublicProfilePage: () => ({
    navigate: vi.fn(),
    profile: {
      username: 'bob',
      avatar: null,
      team: null,
      date_joined: '2024-01-15T00:00:00Z',
      stats: {
        total_games_played: 20,
        total_wins: 10,
        total_points: 2000,
        win_rate: 50,
        best_score: 400,
        avg_score_per_game: 100,
        accuracy: 60,
        avg_response_time: 4.5,
        achievements_unlocked: 5,
        achievements_total: 15,
      },
    },
    loading: false,
    error: null,
  }),
}));

vi.mock('@/utils/format', () => ({
  formatLocalDate: () => '15 janvier 2024',
}));

class PublicProfilePageIntTest extends BasePageTest {
  protected getRoute() { return '/profile/:userId'; }
  protected getComponent() { return PublicProfilePage; }

  run() {
    describe('PublicProfilePage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersUsername();
      this.testRendersStats();
      this.testRendersMemberSince();
    });
  }

  private testRendersUsername() {
    it('affiche le nom d\'utilisateur', () => {
      this.renderPage(['/profile/2']);
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }

  private testRendersStats() {
    it('affiche les statistiques', () => {
      this.renderPage(['/profile/2']);
      expect(screen.getByText('Statistiques', { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Parties jouées')).toBeInTheDocument();
      expect(screen.getByText('Victoires')).toBeInTheDocument();
    });
  }

  private testRendersMemberSince() {
    it('affiche la date d\'inscription', () => {
      this.renderPage(['/profile/2']);
      expect(screen.getByText(/Membre depuis/)).toBeInTheDocument();
    });
  }
}

new PublicProfilePageIntTest().run();
