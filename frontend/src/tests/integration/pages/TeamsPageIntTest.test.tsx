import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import TeamsPage from '@/pages/TeamsPage';

vi.mock('@/hooks/pages/useTeamsPage', () => ({
  useTeamsPage: () => ({
    user: { id: 1, username: 'alice' },
    activeTab: 'browse',
    setActiveTab: vi.fn(),
    message: null,
    setMessage: vi.fn(),
    newTeamName: '',
    setNewTeamName: vi.fn(),
    newTeamDescription: '',
    setNewTeamDescription: vi.fn(),
    creating: false,
    allTeams: [
      { id: 'team-1', name: 'Team Alpha', description: 'Test team', member_count: 3, avatar: null, owner: { id: 1, username: 'alice' }, members_list: [], total_games: 5, total_wins: 2, total_points: 5000, created_at: '2024-01-01', updated_at: '2024-01-01' },
    ],
    loading: false,
    handleCreateTeam: vi.fn(),
    handleJoinTeam: vi.fn(),
    isInTeam: vi.fn(() => false),
  }),
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string) => url ?? '',
}));

class TeamsPageIntTest extends BasePageTest {
  protected getRoute() { return '/teams'; }
  protected getComponent() { return TeamsPage; }

  run() {
    describe('TeamsPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTitle();
      this.testRendersTeams();
      this.testRendersTabs();
    });
  }

  private testRendersTitle() {
    it('affiche le titre', () => {
      this.renderPage();
      expect(screen.getByText('Équipes')).toBeInTheDocument();
    });
  }

  private testRendersTeams() {
    it('affiche les équipes', () => {
      this.renderPage();
      expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    });
  }

  private testRendersTabs() {
    it('affiche les onglets', () => {
      this.renderPage();
      expect(screen.getByText(/Parcourir/)).toBeInTheDocument();
    });
  }
}

new TeamsPageIntTest().run();
