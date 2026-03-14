import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('@/services/socialService', () => ({
  friendshipService: {
    getFriends: vi.fn(),
  },
}));

vi.mock('@/services/invitationService', () => ({
  invitationService: {
    invite: vi.fn(),
  },
}));

vi.mock('@/utils/apiError', () => ({
  getApiErrorMessage: (_err: unknown, fallback: string) => fallback,
}));

import InviteFriendsModal from '@/components/game/InviteFriendsModal';
import { friendshipService } from '@/services/socialService';
import { invitationService } from '@/services/invitationService';

class InviteFriendsModalTest {
  run() {
    describe('InviteFriendsModal', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      this.testRendersModal();
      this.testShowsFriends();
      this.testInviteFriend();
      this.testCloseOnEscape();
      this.testEmptyState();
      this.testSearchFilter();
    });
  }

  private testRendersModal() {
    it('affiche le titre "Inviter des amis"', async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([]);
      render(<InviteFriendsModal roomCode="XYZ" onClose={() => {}} />);
      expect(screen.getByText('Inviter des amis')).toBeInTheDocument();
    });
  }

  private testShowsFriends() {
    it('affiche la liste des amis', async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([
        { id: 1, user: { id: 10, username: 'alice' } },
        { id: 2, user: { id: 20, username: 'bob' } },
      ] as any);
      render(<InviteFriendsModal roomCode="XYZ" onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('alice')).toBeInTheDocument();
        expect(screen.getByText('bob')).toBeInTheDocument();
      });
    });
  }

  private testInviteFriend() {
    it('envoie une invitation au clic', async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([
        { id: 1, user: { id: 10, username: 'alice' } },
      ] as any);
      vi.mocked(invitationService.invite).mockResolvedValue({} as any);
      render(<InviteFriendsModal roomCode="XYZ" onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('alice')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Inviter'));
      await waitFor(() => {
        expect(invitationService.invite).toHaveBeenCalledWith('XYZ', 'alice');
      });
    });
  }

  private testCloseOnEscape() {
    it('ferme la modal sur Escape', async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([]);
      const onClose = vi.fn();
      render(<InviteFriendsModal roomCode="XYZ" onClose={onClose} />);
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(onClose).toHaveBeenCalled();
    });
  }

  private testEmptyState() {
    it("affiche 'pas encore d'amis' si liste vide", async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([]);
      render(<InviteFriendsModal roomCode="XYZ" onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/pas encore d'amis/i)).toBeInTheDocument();
      });
    });
  }

  private testSearchFilter() {
    it('filtre les amis par recherche', async () => {
      vi.mocked(friendshipService.getFriends).mockResolvedValue([
        { id: 1, user: { id: 10, username: 'alice' } },
        { id: 2, user: { id: 20, username: 'bob' } },
      ] as any);
      render(<InviteFriendsModal roomCode="XYZ" onClose={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('alice')).toBeInTheDocument();
      });
      fireEvent.change(screen.getByPlaceholderText(/Rechercher/), { target: { value: 'ali' } });
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.queryByText('bob')).not.toBeInTheDocument();
    });
  }
}

new InviteFriendsModalTest().run();
