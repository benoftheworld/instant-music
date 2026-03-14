import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import JoinGamePage from '@/pages/game/JoinGamePage';

vi.mock('@/hooks/pages/useJoinGamePage', () => ({
  useJoinGamePage: () => ({
    navigate: vi.fn(),
    roomCode: '',
    setRoomCode: vi.fn(),
    publicGames: [],
    publicLoading: false,
    publicSearch: '',
    setPublicSearch: vi.fn(),
    activeTab: 'public',
    setActiveTab: vi.fn(),
    loading: false,
    error: null,
    setError: vi.fn(),
    joinByCode: vi.fn(),
    handleJoinGame: vi.fn(),
  }),
}));

class JoinGamePageIntTest extends BasePageTest {
  protected getRoute() { return '/game/join'; }
  protected getComponent() { return JoinGamePage; }

  run() {
    describe('JoinGamePage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTitle();
      this.testRendersTabs();
    });
  }

  private testRendersTitle() {
    it('affiche le titre', () => {
      this.renderPage();
      expect(screen.getByText('Rejoindre une partie')).toBeInTheDocument();
    });
  }

  private testRendersTabs() {
    it('affiche les onglets', () => {
      this.renderPage();
      expect(screen.getByText(/Parties publiques/)).toBeInTheDocument();
      expect(screen.getByText(/Code de salle/)).toBeInTheDocument();
    });
  }
}

new JoinGamePageIntTest().run();
