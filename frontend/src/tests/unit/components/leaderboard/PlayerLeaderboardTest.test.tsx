import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

import PlayerLeaderboard from '@/components/leaderboard/PlayerLeaderboard';

function makePlayers(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    user_id: i + 1,
    username: `player${i + 1}`,
    avatar: null,
    total_points: (n - i) * 100,
    total_games: 10,
    total_wins: 5,
    team_name: null,
    team_id: null,
  }));
}

class PlayerLeaderboardTest {
  run() {
    describe('PlayerLeaderboard', () => {
      this.testRendersPlayers();
      this.testPodiumForTop3();
      this.testMedals();
    });
  }

  private testRendersPlayers() {
    it('affiche les joueurs', () => {
      render(
        <MemoryRouter>
          <PlayerLeaderboard
            players={makePlayers(5) as any}
            page={1}
            totalCount={5}
            pageSize={10}
            onPrev={() => {}}
            onNext={() => {}}
          />
        </MemoryRouter>,
      );
      expect(screen.getAllByText('player1').length).toBeGreaterThan(0);
      expect(screen.getAllByText('player5').length).toBeGreaterThan(0);
    });
  }

  private testPodiumForTop3() {
    it('affiche le podium pour les 3 premiers', () => {
      render(
        <MemoryRouter>
          <PlayerLeaderboard
            players={makePlayers(5) as any}
            page={1}
            totalCount={5}
            pageSize={10}
            onPrev={() => {}}
            onNext={() => {}}
          />
        </MemoryRouter>,
      );
      expect(screen.getByText('👑')).toBeInTheDocument();
    });
  }

  private testMedals() {
    it('affiche les médailles', () => {
      render(
        <MemoryRouter>
          <PlayerLeaderboard
            players={makePlayers(5) as any}
            page={1}
            totalCount={5}
            pageSize={10}
            onPrev={() => {}}
            onNext={() => {}}
          />
        </MemoryRouter>,
      );
      expect(screen.getByText('🥇')).toBeInTheDocument();
    });
  }
}

new PlayerLeaderboardTest().run();
