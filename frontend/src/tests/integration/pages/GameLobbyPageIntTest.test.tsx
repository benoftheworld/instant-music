import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import GameLobbyPage from '@/pages/game/GameLobbyPage';

vi.mock('@/hooks/pages/useGameLobbyPage', () => ({
  useGameLobbyPage: () => ({
    roomCode: 'ABC123',
    game: {
      room_code: 'ABC123',
      host: 1,
      host_username: 'alice',
      status: 'waiting',
      mode: 'classique',
      players: [
        { id: 1, username: 'alice', score: 0 },
        { id: 2, username: 'bob', score: 0 },
      ],
    },
    loading: false,
    error: null,
    startError: null,
    startingGame: false,
    selectedPlaylist: null,
    showPlaylistSelector: false,
    setShowPlaylistSelector: vi.fn(),
    copyMessage: '',
    showInviteModal: false,
    setShowInviteModal: vi.fn(),
    isConnected: true,
    isHost: true,
    isSolo: false,
    handleSelectPlaylist: vi.fn(),
    handleStartGame: vi.fn(),
    handleLeaveGame: vi.fn(),
    copyRoomCode: vi.fn(),
    shareGame: vi.fn(),
  }),
}));

class GameLobbyPageIntTest extends BasePageTest {
  protected getRoute() { return '/game/:roomCode/lobby'; }
  protected getComponent() { return GameLobbyPage; }

  run() {
    describe('GameLobbyPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersLobby();
      this.testRendersPlayers();
    });
  }

  private testRendersLobby() {
    it('affiche le lobby avec le code de salle', () => {
      this.renderPage(['/game/ABC123/lobby']);
      expect(screen.getByText('ABC123')).toBeInTheDocument();
    });
  }

  private testRendersPlayers() {
    it('affiche les joueurs', () => {
      this.renderPage(['/game/ABC123/lobby']);
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }
}

new GameLobbyPageIntTest().run();
