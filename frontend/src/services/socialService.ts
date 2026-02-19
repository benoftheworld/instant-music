/**
 * Service for friendship and team management
 */
import { api } from './api';
import type { Friendship, Friend, Team, UserMinimal } from '@/types';

// ─── Friendship API ────────────────────────────────────────────────────────

export const friendshipService = {
  /**
   * Get list of all friends (accepted friendships)
   */
  async getFriends(): Promise<Friend[]> {
    const response = await api.get('/users/friends/');
    return response.data;
  },

  /**
   * Get pending friend requests received
   */
  async getPendingRequests(): Promise<Friendship[]> {
    const response = await api.get('/users/friends/pending/');
    return response.data;
  },

  /**
   * Get friend requests sent
   */
  async getSentRequests(): Promise<Friendship[]> {
    const response = await api.get('/users/friends/sent/');
    return response.data;
  },

  /**
   * Send a friend request
   */
  async sendRequest(username: string): Promise<Friendship> {
    const response = await api.post('/users/friends/send_request/', { username });
    return response.data;
  },

  /**
   * Accept a friend request
   */
  async acceptRequest(friendshipId: number): Promise<Friendship> {
    const response = await api.post(`/users/friends/${friendshipId}/accept/`);
    return response.data;
  },

  /**
   * Reject a friend request
   */
  async rejectRequest(friendshipId: number): Promise<void> {
    await api.post(`/users/friends/${friendshipId}/reject/`);
  },

  /**
   * Remove a friend
   */
  async removeFriend(friendshipId: number): Promise<void> {
    await api.delete(`/users/friends/${friendshipId}/remove/`);
  },

  /**
   * Search users by username
   */
  async searchUsers(query: string): Promise<UserMinimal[]> {
    const response = await api.get('/users/search/', { params: { q: query } });
    return response.data;
  },
};

// ─── Team API ──────────────────────────────────────────────────────────────

export const teamService = {
  /**
   * Get user's teams
   */
  async getMyTeams(): Promise<Team[]> {
    const response = await api.get('/users/teams/');
    return response.data;
  },

  /**
   * Get a specific team
   */
  async getTeam(teamId: number): Promise<Team> {
    const response = await api.get(`/users/teams/${teamId}/`);
    return response.data;
  },

  /**
   * Browse all teams
   */
  async browseTeams(): Promise<Team[]> {
    const response = await api.get('/users/teams/browse/');
    return response.data;
  },

  /**
   * Create a new team
   */
  async createTeam(data: { name: string; description?: string }): Promise<Team> {
    const response = await api.post('/users/teams/', data);
    return response.data;
  },

  /**
   * Join a team
   */
  async joinTeam(teamId: number): Promise<Team> {
    const response = await api.post(`/users/teams/${teamId}/join/`);
    return response.data;
  },

  /**
   * Leave a team
   */
  async leaveTeam(teamId: number): Promise<void> {
    await api.post(`/users/teams/${teamId}/leave/`);
  },

  /**
   * Invite a user to a team (admin/owner only)
   */
  async inviteToTeam(teamId: number, username: string): Promise<void> {
    await api.post(`/users/teams/${teamId}/invite/`, { username });
  },
  
  /**
   * Update a team member role
   */
  async updateMemberRole(teamId: number, memberId: number, role: string): Promise<void> {
    await api.post(`/users/teams/${teamId}/update_member/`, { member_id: memberId, role });
  },

  /**
   * Remove a member from the team (admin/owner only)
   */
  async removeMember(teamId: number, memberId: number): Promise<void> {
    await api.post(`/users/teams/${teamId}/remove_member/`, { member_id: memberId });
  },

  /**
   * Get pending join requests for a team
   */
  async getJoinRequests(teamId: number) {
    const response = await api.get(`/users/teams/${teamId}/requests/`);
    return response.data;
  },

  /**
   * Update team info (description/avatar) - multipart
   */
  async updateTeam(teamId: number, data: FormData) {
    const response = await api.patch(`/users/teams/${teamId}/edit/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
