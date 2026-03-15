import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import HomePage from '@/pages/HomePage';

// Mock authStore with controllable state
const mockIsAuthenticated = vi.fn(() => false);
vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: any) => selector({ isAuthenticated: mockIsAuthenticated() }),
}));

vi.mock('@/components/home/RecentGames', () => ({
  default: () => <div data-testid="recent-games">RecentGames</div>,
}));

vi.mock('@/components/home/TopPlayers', () => ({
  default: () => <div data-testid="top-players">TopPlayers</div>,
}));

class HomePageIntTest extends BasePageTest {
  protected getRoute() { return '/'; }
  protected getComponent() { return HomePage; }

  run() {
    describe('HomePage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
        mockIsAuthenticated.mockReturnValue(false);
      });

      this.testRendersHero();
      this.testGuestCTAs();
      this.testGuestLoginForm();
      this.testAuthenticatedCTAs();
      this.testShowsRecentGamesWhenAuthenticated();
    });
  }

  private testRendersHero() {
    it('affiche le titre principal', () => {
      this.renderPage();
      expect(screen.getByText(/Bienvenue sur/)).toBeInTheDocument();
      expect(screen.getByText('InstantMusic')).toBeInTheDocument();
    });
  }

  private testGuestCTAs() {
    it('affiche le bouton d\'inscription pour les visiteurs', () => {
      this.renderPage();
      expect(screen.getByText('Commencer à jouer')).toBeInTheDocument();
    });
  }

  private testGuestLoginForm() {
    it('affiche un formulaire de connexion pour les visiteurs non connectés', () => {
      this.renderPage();
      expect(screen.getByText('Déjà inscrit ?')).toBeInTheDocument();
      expect(screen.getByLabelText(/Identifiant/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Mot de passe/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Se connecter/ })).toBeInTheDocument();
    });
  }

  private testAuthenticatedCTAs() {
    it('affiche les boutons pour les utilisateurs connectés', () => {
      mockIsAuthenticated.mockReturnValue(true);
      this.renderPage();
      expect(screen.getByText('Créer une partie')).toBeInTheDocument();
      expect(screen.getByText('Rejoindre une partie')).toBeInTheDocument();
    });
  }

  private testShowsRecentGamesWhenAuthenticated() {
    it('affiche les parties récentes pour les utilisateurs connectés', () => {
      mockIsAuthenticated.mockReturnValue(true);
      this.renderPage();
      expect(screen.getByTestId('recent-games')).toBeInTheDocument();
      expect(screen.getByTestId('top-players')).toBeInTheDocument();
    });
  }
}

new HomePageIntTest().run();
