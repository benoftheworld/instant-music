import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/services/gameService', () => ({
  gameService: {
    getRecentGames: vi.fn(),
  },
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

vi.mock('@/constants/gameModes', () => ({
  getModeIcon: () => '🎵',
}));

vi.mock('@/utils/format', () => ({
  formatDate: () => '01/01/2026',
}));

vi.mock('@/constants/queryKeys', () => ({
  QUERY_KEYS: { recentGames: () => ['recentGames'] },
}));

import RecentGames from '@/components/home/RecentGames';
import { gameService } from '@/services/gameService';

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

class RecentGamesTest {
  run() {
    describe('RecentGames', () => {
      this.testEmptyState();
      this.testShowsGames();
    });
  }

  private testEmptyState() {
    it('affiche "Aucune partie récente" si vide', async () => {
      vi.mocked(gameService.getRecentGames).mockResolvedValue([]);
      renderWithProviders(<RecentGames />);
      expect(await screen.findByText('Aucune partie récente')).toBeInTheDocument();
    });
  }

  private testShowsGames() {
    it('affiche les parties récentes', async () => {
      vi.mocked(gameService.getRecentGames).mockResolvedValue([
        {
          id: 1,
          mode: 'classique',
          mode_display: 'Classique',
          player_count: 4,
          winner: { username: 'alice', avatar: null },
          winner_score: 500,
          finished_at: '2026-01-01',
        },
      ] as any);
      renderWithProviders(<RecentGames />);
      expect(await screen.findByText('Classique')).toBeInTheDocument();
      expect(screen.getByText('alice')).toBeInTheDocument();
    });
  }
}

new RecentGamesTest().run();
