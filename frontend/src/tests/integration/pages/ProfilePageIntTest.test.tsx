import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import ProfilePage from '@/pages/ProfilePage';

vi.mock('@/hooks/pages/useProfilePage', () => ({
  useProfilePage: () => ({
    user: { id: 1, username: 'alice', email: 'alice@test.com', avatar: null },
    activeTab: 'stats',
    setActiveTab: vi.fn(),
    achievementFilter: 'all',
    setAchievementFilter: vi.fn(),
    passwordData: { current_password: '', new_password: '', confirm_password: '' },
    setPasswordData: vi.fn(),
    showPasswords: { current: false, new: false, confirm: false },
    setShowPasswords: vi.fn(),
    avatarFile: null,
    avatarPreview: null,
    loading: false,
    message: null,
    passwordMessage: null,
    achievements: [],
    achievementsLoading: false,
    detailedStats: { total_games_played: 10, total_wins: 5, total_points: 1500, win_rate: 50, avg_score_per_game: 150, best_score: 300, total_correct_answers: 40, total_answers: 80, accuracy: 50, avg_response_time: 5.2, achievements_unlocked: 3, achievements_total: 10, recent_games: [] },
    showDeleteZone: false,
    setShowDeleteZone: vi.fn(),
    deleteConfirmText: '',
    setDeleteConfirmText: vi.fn(),
    handleAvatarChange: vi.fn(),
    handleProfileUpdate: vi.fn(),
    handlePasswordChange: vi.fn(),
    handleExportData: vi.fn(),
    handleDeleteAccount: vi.fn(),
    getAchievementProgress: vi.fn(),
    getAchievementProgressLabel: vi.fn(),
    filteredAchievements: [],
    unlockedCount: 3,
    passwordStrength: { score: 0, label: '', color: '' },
    confirmMismatch: false,
  }),
}));

class ProfilePageIntTest extends BasePageTest {
  protected getRoute() { return '/profile'; }
  protected getComponent() { return ProfilePage; }

  run() {
    describe('ProfilePage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersHeader();
      this.testRendersTabs();
    });
  }

  private testRendersHeader() {
    it('affiche le nom d\'utilisateur', () => {
      this.renderPage();
      expect(screen.getByText('alice')).toBeInTheDocument();
    });
  }

  private testRendersTabs() {
    it('affiche les onglets de navigation', () => {
      this.renderPage();
      const buttons = screen.getAllByRole('button');
      const tabTexts = buttons.map((b) => b.textContent);
      expect(tabTexts.some((t) => t?.includes('📊'))).toBe(true);
      expect(tabTexts.some((t) => t?.includes('🏆'))).toBe(true);
      expect(tabTexts.some((t) => t?.includes('👤'))).toBe(true);
      expect(tabTexts.some((t) => t?.includes('🔒'))).toBe(true);
    });
  }
}

new ProfilePageIntTest().run();
