import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { BaseIntegrationTest } from '../base/BaseIntegrationTest';
import { seedDB, getDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import { createTestQueryClient } from '@/tests/shared/renderHelpers';
import FriendsPage from '@/pages/FriendsPage';

vi.mock('@/hooks/pages/useFriendsPage', () => {
  const sentIds = new Set<number>();
  return {
    useFriendsPage: () => ({
      loading: false,
      friends: [
        { friendship_id: 1, user: { id: 2, username: 'bob', avatar: null, total_points: 1200, total_wins: 8 } },
      ],
      pendingRequests: [],
      sentRequests: [...sentIds].map((id) => ({ id, to_user: { id, username: `user-${id}` } })),
      searchResults: [
        { id: 3, username: 'charlie', avatar: null },
      ],
      searchQuery: '',
      setSearchQuery: vi.fn(),
      activeTab: 'friends',
      setActiveTab: vi.fn(),
      message: null,
      setMessage: vi.fn(),
      handleSearch: vi.fn(),
      handleSendRequest: vi.fn((userId: number) => sentIds.add(userId)),
      handleAccept: vi.fn(),
      handleReject: vi.fn(),
      handleRemoveFriend: vi.fn(),
    }),
  };
});

vi.mock('@/utils/format', () => ({
  formatLocalDate: () => '15 janv. 2024',
}));

class FriendshipFlowIntTest extends BaseIntegrationTest {
  run() {
    describe('Friendship Flow (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersFriendsList();
      this.testShowsExistingFriend();
    });
  }

  private renderApp() {
    const queryClient = createTestQueryClient();
    const user = userEvent.setup();
    const result = render(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(
          MemoryRouter,
          { initialEntries: ['/friends'] },
          React.createElement(
            Routes,
            null,
            React.createElement(Route, { path: '/friends', element: React.createElement(FriendsPage) }),
          ),
        ),
      ),
    );
    return { ...result, user };
  }

  private testRendersFriendsList() {
    it('affiche la page d\'amis', () => {
      this.renderApp();
      expect(screen.getByText(/Amis/)).toBeInTheDocument();
    });
  }

  private testShowsExistingFriend() {
    it('affiche un ami existant', () => {
      this.renderApp();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
  }
}

new FriendshipFlowIntTest().run();
