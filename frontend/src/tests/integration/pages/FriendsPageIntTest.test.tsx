import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import FriendsPage from '@/pages/FriendsPage';

vi.mock('@/hooks/pages/useFriendsPage', () => ({
  useFriendsPage: () => ({
    loading: false,
    friends: [
      { friendship_id: 1, user: { id: 2, username: 'bob', avatar: null, total_points: 1200, total_wins: 8 } },
    ],
    pendingRequests: [],
    sentRequests: [],
    searchResults: [],
    searchQuery: '',
    setSearchQuery: vi.fn(),
    activeTab: 'friends',
    setActiveTab: vi.fn(),
    message: null,
    setMessage: vi.fn(),
    handleSearch: vi.fn(),
    handleSendRequest: vi.fn(),
    handleAccept: vi.fn(),
    handleReject: vi.fn(),
    handleRemoveFriend: vi.fn(),
  }),
}));

vi.mock('@/utils/format', () => ({
  formatLocalDate: () => '15 janv. 2024',
}));

class FriendsPageIntTest extends BasePageTest {
  protected getRoute() { return '/friends'; }
  protected getComponent() { return FriendsPage; }

  run() {
    describe('FriendsPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersTitle();
      this.testRendersFriends();
      this.testRendersTabs();
    });
  }

  private testRendersTitle() {
    it('affiche le titre', () => {
      this.renderPage();
      expect(screen.getByText(/Amis/)).toBeInTheDocument();
    });
  }

  private testRendersFriends() {
    it('affiche la liste des amis', () => {
      this.renderPage();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }

  private testRendersTabs() {
    it('affiche les onglets', () => {
      this.renderPage();
      expect(screen.getByText(/Mes amis/)).toBeInTheDocument();
    });
  }
}

new FriendsPageIntTest().run();
