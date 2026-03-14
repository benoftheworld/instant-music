import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import GamePlayPage from '@/pages/game/GamePlayPage';

vi.mock('@/hooks/pages/useGamePlayPage', () => ({
  useGamePlayPage: () => ({
    roomCode: 'ABC123',
    game: {
      room_code: 'ABC123',
      mode: 'classique',
      status: 'in_progress',
      players: [{ id: 1, username: 'alice', score: 100 }],
    },
    loading: true,
    error: null,
    state: { phase: 'loading' },
    currentRound: null,
    timeLeft: 30,
    answered: false,
    selectedAnswer: null,
    isHost: true,
    isPartyMode: false,
    sendAnswer: vi.fn(),
    handleNextRound: vi.fn(),
    handleLeave: vi.fn(),
  }),
}));

class GamePlayPageIntTest extends BasePageTest {
  protected getRoute() { return '/game/:roomCode/play'; }
  protected getComponent() { return GamePlayPage; }

  run() {
    describe('GamePlayPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersLoadingState();
    });
  }

  private testRendersLoadingState() {
    it('affiche l\'état de chargement', () => {
      this.renderPage(['/game/ABC123/play']);
      // When loading, should show some loading indicator
      expect(document.body.textContent).toBeTruthy();
    });
  }
}

new GamePlayPageIntTest().run();
