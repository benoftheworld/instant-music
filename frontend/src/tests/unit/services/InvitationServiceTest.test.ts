import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { invitationService } from '@/services/invitationService';
import { api } from '@/services/api';
import { createGameInvitation } from '@/tests/shared/factories';

class InvitationServiceTest extends BaseServiceTest {
  protected name = 'invitationService';

  run() {
    describe('invitationService', () => {
      this.setup(api);

      this.testInvite();
      this.testGetMyInvitations();
      this.testAccept();
      this.testDecline();
      this.testInviteError();
    });
  }

  private testInvite() {
    it('invite — succès', async () => {
      const inv = createGameInvitation();
      this.mockPost('/games/ABC123/invite/', inv);
      const result = await invitationService.invite('ABC123', 'bob');
      expect(result).toEqual(inv);
      expect(api.post).toHaveBeenCalledWith('/games/ABC123/invite/', { username: 'bob' });
    });
  }

  private testGetMyInvitations() {
    it('getMyInvitations — succès', async () => {
      const invitations = [createGameInvitation()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: invitations });
      const result = await invitationService.getMyInvitations();
      expect(result).toEqual(invitations);
    });
  }

  private testAccept() {
    it('accept — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { room_code: 'ABC123', message: 'ok' } });
      const result = await invitationService.accept('inv-1');
      expect(result.room_code).toBe('ABC123');
    });
  }

  private testDecline() {
    it('decline — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { message: 'refusée' } });
      const result = await invitationService.decline('inv-1');
      expect(result.message).toBeTruthy();
    });
  }

  private testInviteError() {
    it('invite — erreur 400', async () => {
      this.mockError('post', 400, { detail: 'Joueur déjà invité.' });
      await expect(invitationService.invite('ABC123', 'bob')).rejects.toThrow();
    });
  }
}

new InvitationServiceTest().run();
