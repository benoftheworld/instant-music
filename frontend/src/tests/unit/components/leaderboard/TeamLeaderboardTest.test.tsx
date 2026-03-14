import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

import TeamLeaderboard from '@/components/leaderboard/TeamLeaderboard';

function makeTeams(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    id: i + 1,
    name: `Team ${i + 1}`,
    avatar: null,
    member_count: 3,
    total_games: 10,
    total_wins: 5,
    win_rate: 50,
    total_points: (n - i) * 200,
  }));
}

class TeamLeaderboardTest {
  run() {
    describe('TeamLeaderboard', () => {
      this.testRendersTeams();
      this.testEmptyState();
    });
  }

  private testRendersTeams() {
    it('affiche les équipes', () => {
      render(
        <MemoryRouter>
          <TeamLeaderboard
            teams={makeTeams(3) as any}
            page={1}
            totalCount={3}
            pageSize={10}
            onPrev={() => {}}
            onNext={() => {}}
          />
        </MemoryRouter>,
      );
      expect(screen.getByText('Team 1')).toBeInTheDocument();
      expect(screen.getByText('Team 3')).toBeInTheDocument();
    });
  }

  private testEmptyState() {
    it('affiche "Aucune équipe" si vide', () => {
      render(
        <MemoryRouter>
          <TeamLeaderboard
            teams={[]}
            page={1}
            totalCount={0}
            pageSize={10}
            onPrev={() => {}}
            onNext={() => {}}
          />
        </MemoryRouter>,
      );
      expect(screen.getByText(/Aucune équipe/)).toBeInTheDocument();
    });
  }
}

new TeamLeaderboardTest().run();
