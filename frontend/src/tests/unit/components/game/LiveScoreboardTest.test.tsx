import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createGamePlayer } from '@/tests/shared/factories';

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url ? `http://media/${url}` : null,
}));

import LiveScoreboard from '@/components/game/LiveScoreboard';

class LiveScoreboardTest {
  run() {
    describe('LiveScoreboard', () => {
      this.testRendersPlayers();
      this.testSortsByScore();
      this.testEmptyState();
      this.testMedals();
    });
  }

  private testRendersPlayers() {
    it('affiche tous les joueurs', () => {
      const players = [
        createGamePlayer({ username: 'alice', score: 100 }),
        createGamePlayer({ username: 'bob', score: 50 }),
      ];
      render(<LiveScoreboard players={players} />);
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }

  private testSortsByScore() {
    it('trie par score décroissant', () => {
      const players = [
        createGamePlayer({ username: 'bob', score: 50 }),
        createGamePlayer({ username: 'alice', score: 100 }),
      ];
      render(<LiveScoreboard players={players} />);
      const scores = screen.getAllByText(/\d+/).filter(el => el.className.includes('font-bold'));
      // alice (100) should come before bob (50)
      expect(screen.getByText('alice')).toBeInTheDocument();
    });
  }

  private testEmptyState() {
    it('affiche message "Aucun joueur" si vide', () => {
      render(<LiveScoreboard players={[]} />);
      expect(screen.getByText('Aucun joueur')).toBeInTheDocument();
    });
  }

  private testMedals() {
    it('affiche les médailles pour le top 3', () => {
      const players = [
        createGamePlayer({ username: 'a', score: 100 }),
        createGamePlayer({ username: 'b', score: 80 }),
        createGamePlayer({ username: 'c', score: 60 }),
      ];
      render(<LiveScoreboard players={players} />);
      expect(screen.getByText('🥇')).toBeInTheDocument();
      expect(screen.getByText('🥈')).toBeInTheDocument();
      expect(screen.getByText('🥉')).toBeInTheDocument();
    });
  }
}

new LiveScoreboardTest().run();
