import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/store/notificationStore', () => ({
  useNotificationStore: vi.fn(() => ({
    invitations: [],
    friendRequests: [],
    socialNotifications: [],
    removeInvitation: vi.fn(),
    removeFriendRequest: vi.fn(),
    removeSocialNotification: vi.fn(),
  })),
}));

vi.mock('@/services/invitationService', () => ({
  invitationService: { accept: vi.fn(), decline: vi.fn() },
}));

vi.mock('@/services/socialService', () => ({
  friendshipService: { acceptRequest: vi.fn(), rejectRequest: vi.fn() },
}));

vi.mock('@/utils/apiError', () => ({
  getApiErrorMessage: () => 'Erreur',
}));

vi.mock('@/constants/gameModes', () => ({
  getModeLabel: () => 'Classique',
}));

import NotificationBell from '@/components/layout/NotificationBell';
import { useNotificationStore } from '@/store/notificationStore';

class NotificationBellTest {
  run() {
    describe('NotificationBell', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      this.testRendersBellEmpty();
      this.testShowsBadge();
      this.testOpensDropdown();
    });
  }

  private testRendersBellEmpty() {
    it('affiche le bouton cloche sans badge quand vide', () => {
      render(
        <MemoryRouter>
          <NotificationBell />
        </MemoryRouter>,
      );
      expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
    });
  }

  private testShowsBadge() {
    it('affiche le badge avec le nombre de notifications', () => {
      vi.mocked(useNotificationStore).mockReturnValue({
        invitations: [{ id: 1 }],
        friendRequests: [{ id: 2 }],
        socialNotifications: [],
        removeInvitation: vi.fn(),
        removeFriendRequest: vi.fn(),
        removeSocialNotification: vi.fn(),
      } as any);
      render(
        <MemoryRouter>
          <NotificationBell />
        </MemoryRouter>,
      );
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  }

  private testOpensDropdown() {
    it('ouvre le dropdown au clic', () => {
      vi.mocked(useNotificationStore).mockReturnValue({
        invitations: [{ id: 1, sender: { username: 'alice' }, game_mode: 'classique', room_code: 'ABC' }],
        friendRequests: [],
        socialNotifications: [],
        removeInvitation: vi.fn(),
        removeFriendRequest: vi.fn(),
        removeSocialNotification: vi.fn(),
      } as any);
      render(
        <MemoryRouter>
          <NotificationBell />
        </MemoryRouter>,
      );
      fireEvent.click(screen.getByLabelText(/notification/i));
      expect(screen.getByText(/alice/)).toBeInTheDocument();
    });
  }
}

new NotificationBellTest().run();
