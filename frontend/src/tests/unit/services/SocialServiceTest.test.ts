import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { friendshipService, teamService } from '@/services/socialService';
import { api } from '@/services/api';
import { createFriend, createFriendship, createTeam } from '@/tests/shared/factories';

class SocialServiceTest extends BaseServiceTest {
  protected name = 'socialService';

  run() {
    describe('friendshipService', () => {
      this.setup(api);

      this.testGetFriends();
      this.testGetPendingRequests();
      this.testGetSentRequests();
      this.testSendRequest();
      this.testAcceptRequest();
      this.testRejectRequest();
      this.testRemoveFriend();
      this.testSearchUsers();
      this.testSendRequestError();
    });

    describe('teamService', () => {
      this.setup(api);

      this.testGetMyTeams();
      this.testGetTeam();
      this.testBrowseTeams();
      this.testCreateTeam();
      this.testJoinTeam();
      this.testLeaveTeam();
      this.testInviteToTeam();
      this.testUpdateMemberRole();
      this.testRemoveMember();
      this.testGetJoinRequests();
      this.testApproveJoinRequest();
      this.testRejectJoinRequest();
      this.testUpdateTeam();
      this.testDissolveTeam();
      this.testGetTeamError();
    });
  }

  // ── Friendship ─────────────────────────────────

  private testGetFriends() {
    it('getFriends — succès', async () => {
      const friends = [createFriend()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: friends });
      const result = await friendshipService.getFriends();
      expect(result).toEqual(friends);
    });
  }

  private testGetPendingRequests() {
    it('getPendingRequests — succès', async () => {
      const requests = [createFriendship()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: requests });
      const result = await friendshipService.getPendingRequests();
      expect(result).toEqual(requests);
    });
  }

  private testGetSentRequests() {
    it('getSentRequests — succès', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
      const result = await friendshipService.getSentRequests();
      expect(result).toEqual([]);
    });
  }

  private testSendRequest() {
    it('sendRequest — succès', async () => {
      const friendship = createFriendship();
      this.mockPost('/users/friends/send_request/', friendship);
      const result = await friendshipService.sendRequest('bob');
      expect(result).toEqual(friendship);
    });
  }

  private testAcceptRequest() {
    it('acceptRequest — succès', async () => {
      const friendship = createFriendship({ status: 'accepted' });
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: friendship });
      const result = await friendshipService.acceptRequest(1);
      expect(result.status).toBe('accepted');
    });
  }

  private testRejectRequest() {
    it('rejectRequest — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await friendshipService.rejectRequest(1);
      expect(api.post).toHaveBeenCalledWith('/users/friends/1/reject/');
    });
  }

  private testRemoveFriend() {
    it('removeFriend — succès', async () => {
      (api.delete as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await friendshipService.removeFriend(1);
      expect(api.delete).toHaveBeenCalledWith('/users/friends/1/remove/');
    });
  }

  private testSearchUsers() {
    it('searchUsers — succès', async () => {
      const users = [{ id: 1, username: 'alice' }];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: users });
      const result = await friendshipService.searchUsers('ali');
      expect(result).toEqual(users);
    });
  }

  private testSendRequestError() {
    it('sendRequest — erreur 400', async () => {
      this.mockError('post', 400, { detail: 'Déjà amis.' });
      await expect(friendshipService.sendRequest('bob')).rejects.toThrow();
    });
  }

  // ── Teams ──────────────────────────────────────

  private testGetMyTeams() {
    it('getMyTeams — succès', async () => {
      const teams = [createTeam()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: teams });
      const result = await teamService.getMyTeams();
      expect(result).toEqual(teams);
    });
  }

  private testGetTeam() {
    it('getTeam — succès', async () => {
      const team = createTeam();
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: team });
      const result = await teamService.getTeam('team-1');
      expect(result).toEqual(team);
    });
  }

  private testBrowseTeams() {
    it('browseTeams — succès', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
      const result = await teamService.browseTeams();
      expect(result).toEqual([]);
    });
  }

  private testCreateTeam() {
    it('createTeam — succès', async () => {
      const team = createTeam({ name: 'New Team' });
      this.mockPost('/users/teams/', team);
      const result = await teamService.createTeam({ name: 'New Team' });
      expect(result.name).toBe('New Team');
    });
  }

  private testJoinTeam() {
    it('joinTeam — succès', async () => {
      const team = createTeam();
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: team });
      const result = await teamService.joinTeam('team-1');
      expect(result).toEqual(team);
    });
  }

  private testLeaveTeam() {
    it('leaveTeam — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await teamService.leaveTeam('team-1');
      expect(api.post).toHaveBeenCalledWith('/users/teams/team-1/leave/');
    });
  }

  private testInviteToTeam() {
    it('inviteToTeam — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await teamService.inviteToTeam('team-1', 'bob');
      expect(api.post).toHaveBeenCalledWith('/users/teams/team-1/invite/', { username: 'bob' });
    });
  }

  private testUpdateMemberRole() {
    it('updateMemberRole — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await teamService.updateMemberRole('team-1', 2, 'admin');
      expect(api.post).toHaveBeenCalledWith('/users/teams/team-1/update_member/', { member_id: 2, role: 'admin' });
    });
  }

  private testRemoveMember() {
    it('removeMember — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await teamService.removeMember('team-1', 2);
      expect(api.post).toHaveBeenCalledWith('/users/teams/team-1/remove_member/', { member_id: 2 });
    });
  }

  private testGetJoinRequests() {
    it('getJoinRequests — succès', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
      const result = await teamService.getJoinRequests('team-1');
      expect(result).toEqual([]);
    });
  }

  private testApproveJoinRequest() {
    it('approveJoinRequest — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { detail: 'ok' } });
      const result = await teamService.approveJoinRequest('team-1', 5);
      expect(result).toBeDefined();
    });
  }

  private testRejectJoinRequest() {
    it('rejectJoinRequest — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { detail: 'ok' } });
      const result = await teamService.rejectJoinRequest('team-1', 5);
      expect(result).toBeDefined();
    });
  }

  private testUpdateTeam() {
    it('updateTeam — succès', async () => {
      (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      const formData = new FormData();
      await teamService.updateTeam('team-1', formData);
      expect(api.patch).toHaveBeenCalled();
    });
  }

  private testDissolveTeam() {
    it('dissolveTeam — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await teamService.dissolveTeam('team-1');
      expect(api.post).toHaveBeenCalledWith('/users/teams/team-1/dissolve/');
    });
  }

  private testGetTeamError() {
    it('getTeam — erreur 404', async () => {
      this.mockError('get', 404, { detail: 'Introuvable.' });
      await expect(teamService.getTeam('nope')).rejects.toThrow();
    });
  }
}

new SocialServiceTest().run();
