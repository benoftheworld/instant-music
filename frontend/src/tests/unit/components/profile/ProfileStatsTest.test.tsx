import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProfileStats from '@/components/profile/ProfileStats';

function makeUser(overrides = {}) {
  return {
    total_games_played: 42,
    total_wins: 10,
    win_rate: 23.8,
    total_points: 1500,
    ...overrides,
  } as any;
}

function makeDetailedStats(overrides = {}) {
  return {
    avg_score_per_game: 357.14,
    best_score: 800,
    avg_response_time: 3.2,
    total_answers: 200,
    total_correct_answers: 120,
    accuracy: 60.0,
    achievements_unlocked: 5,
    achievements_total: 20,
    ...overrides,
  };
}

class ProfileStatsTest {
  run() {
    describe('ProfileStats', () => {
      this.testRendersStatCards();
      this.testRendersDetailedStats();
      this.testLoadingState();
    });
  }

  private testRendersStatCards() {
    it('affiche les cartes de stats principales', () => {
      render(<ProfileStats user={makeUser()} detailedStats={makeDetailedStats() as any} />);
      expect(screen.getByText('Parties jouées')).toBeInTheDocument();
      expect(screen.getByText('Victoires')).toBeInTheDocument();
      expect(screen.getByText('Points totaux')).toBeInTheDocument();
    });
  }

  private testRendersDetailedStats() {
    it('affiche les stats détaillées', () => {
      render(<ProfileStats user={makeUser()} detailedStats={makeDetailedStats() as any} />);
      expect(screen.getByText('Score moyen')).toBeInTheDocument();
      expect(screen.getByText('Meilleur score')).toBeInTheDocument();
      expect(screen.getByText('Temps moyen')).toBeInTheDocument();
    });
  }

  private testLoadingState() {
    it('affiche le chargement si pas de stats détaillées', () => {
      render(<ProfileStats user={makeUser()} detailedStats={null} />);
      expect(screen.getByText(/Chargement des statistiques/)).toBeInTheDocument();
    });
  }
}

new ProfileStatsTest().run();
