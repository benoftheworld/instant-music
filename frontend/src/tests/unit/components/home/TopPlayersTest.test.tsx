import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/services/gameService', () => ({
  gameService: {
    getTopPlayers: vi.fn(),
  },
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

vi.mock('@/constants/queryKeys', () => ({
  QUERY_KEYS: { topPlayers: () => ['topPlayers'] },
}));

import TopPlayers from '@/components/home/TopPlayers';
import { gameService } from '@/services/gameService';

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

class TopPlayersTest {
  run() {
    describe('TopPlayers', () => {
      this.testEmptyState();
      this.testShowsPlayers();
    });
  }

  private testEmptyState() {
    it('affiche "Aucun joueur" si vide', async () => {
      vi.mocked(gameService.getTopPlayers).mockResolvedValue([]);
      renderWithProviders(<TopPlayers />);
      expect(await screen.findByText(/Aucun joueur/)).toBeInTheDocument();
    });
  }

  private testShowsPlayers() {
    it('affiche les meilleurs joueurs', async () => {
      vi.mocked(gameService.getTopPlayers).mockResolvedValue([
        {
          user_id: 1,
          username: 'alice',
          avatar: null,
          total_games: 10,
          total_wins: 5,
          total_points: 1000,
        },
      ] as any);
      renderWithProviders(<TopPlayers />);
      expect(await screen.findByText('alice')).toBeInTheDocument();
      expect(screen.getByText('1000')).toBeInTheDocument();
    });
  }
}

new TopPlayersTest().run();
