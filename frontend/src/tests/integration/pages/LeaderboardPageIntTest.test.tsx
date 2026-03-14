import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import LeaderboardPage from '@/pages/LeaderboardPage';

vi.mock('@/hooks/pages/useLeaderboardPage', () => ({
  useLeaderboardPage: () => ({
    user: { id: 1, username: 'alice' },
    selectedMode: 'general',
    page: 1,
    pageSize: 50,
    goNext: vi.fn(),
    goPrev: vi.fn(),
    players: [
      { rank: 1, user_id: 1, username: 'alice', total_points: 1500, avatar: null, total_wins: 10, total_games_played: 20, win_rate: 50 },
      { rank: 2, user_id: 2, username: 'bob', total_points: 1200, avatar: null, total_wins: 8, total_games_played: 18, win_rate: 44 },
    ],
    teams: [],
    totalCount: 2,
    loading: false,
    error: null,
    handleModeChange: vi.fn(),
    primaryTabs: [
      { value: 'general', label: 'Général', icon: '🌍' },
      { value: 'teams', label: 'Équipes', icon: '🛡️' },
    ],
    modeTabs: [
      { value: 'classique', label: 'Classique', icon: '🎵' },
      { value: 'rapide', label: 'Rapide', icon: '⚡' },
    ],
    subtitleMap: { general: 'Classement général de tous les joueurs' },
  }),
}));

vi.mock('@/components/ui', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/components/ui')>();
  return {
    ...actual,
    LoadingState: ({ message }: any) => <div>{message}</div>,
  };
});

class LeaderboardPageIntTest extends BasePageTest {
  protected getRoute() { return '/leaderboard'; }
  protected getComponent() { return LeaderboardPage; }

  run() {
    describe('LeaderboardPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTitle();
      this.testRendersTabs();
      this.testRendersPlayers();
    });
  }

  private testRendersTitle() {
    it('affiche le titre du classement', () => {
      this.renderPage();
      expect(screen.getAllByText(/Classement/).length).toBeGreaterThan(0);
    });
  }

  private testRendersTabs() {
    it('affiche les onglets', () => {
      this.renderPage();
      expect(screen.getByText('Général')).toBeInTheDocument();
      expect(screen.getByText('Équipes')).toBeInTheDocument();
    });
  }

  private testRendersPlayers() {
    it('affiche les joueurs du classement', () => {
      this.renderPage();
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }
}

new LeaderboardPageIntTest().run();
