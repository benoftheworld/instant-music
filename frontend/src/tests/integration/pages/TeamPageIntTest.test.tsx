import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import TeamPage from '@/pages/TeamPage';

vi.mock('@/hooks/pages/useTeamPage', () => ({
  useTeamPage: () => ({
    team: {
      id: 'team-1',
      name: 'Team Alpha',
      description: 'Une équipe de test',
      avatar: null,
      member_count: 2,
      total_games: 20,
      total_wins: 12,
      total_points: 5000,
      members_list: [
        { id: 1, user: { id: 1, username: 'alice', avatar: null, total_points: 3000, total_wins: 8 }, role: 'owner' },
        { id: 2, user: { id: 2, username: 'bob', avatar: null, total_points: 2000, total_wins: 4 }, role: 'member' },
      ],
    },
    loading: false,
    processing: false,
    message: null,
    setMessage: vi.fn(),
    editing: false,
    setEditing: vi.fn(),
    editDescription: '',
    setEditDescription: vi.fn(),
    setEditAvatarFile: vi.fn(),
    joinRequests: [],
    requestsLoading: false,
    canManage: () => true,
    isOwner: true,
    roleLabel: (r: string) => r === 'owner' ? 'Propriétaire' : 'Membre',
    handleChangeRole: vi.fn(),
    handleRemove: vi.fn(),
    handleApproveRequest: vi.fn(),
    handleRejectRequest: vi.fn(),
    handleEditSubmit: vi.fn(),
    handleDissolve: vi.fn(),
  }),
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string) => url ?? '',
}));

class TeamPageIntTest extends BasePageTest {
  protected getRoute() { return '/teams/:teamId'; }
  protected getComponent() { return TeamPage; }

  run() {
    describe('TeamPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTeamName();
      this.testRendersMembers();
      this.testRendersDescription();
    });
  }

  private testRendersTeamName() {
    it('affiche le nom de l\'équipe', () => {
      this.renderPage(['/teams/team-1']);
      expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    });
  }

  private testRendersMembers() {
    it('affiche les membres', () => {
      this.renderPage(['/teams/team-1']);
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }

  private testRendersDescription() {
    it('affiche la description', () => {
      this.renderPage(['/teams/team-1']);
      expect(screen.getByText('Une équipe de test')).toBeInTheDocument();
    });
  }
}

new TeamPageIntTest().run();
