/**
 * Service for game invitations
 */
import { api } from './api';
import type { GameInvitation } from '@/types';

export const invitationService = {
  /**
   * Send a game invitation to a friend (host only)
   */
  async invite(roomCode: string, username: string): Promise<GameInvitation> {
    const response = await api.post<GameInvitation>(`/games/${roomCode}/invite/`, {
      username,
    });
    return response.data;
  },

  /**
   * List pending invitations received by the current user
   */
  async getMyInvitations(): Promise<GameInvitation[]> {
    const response = await api.get<GameInvitation[]>('/games/my-invitations/');
    return response.data;
  },

  /**
   * Accept an invitation and join the lobby
   */
  async accept(invitationId: string): Promise<{ room_code: string; message: string }> {
    const response = await api.post(`/games/invitations/${invitationId}/accept/`);
    return response.data;
  },

  /**
   * Decline an invitation
   */
  async decline(invitationId: string): Promise<{ message: string }> {
    const response = await api.post(`/games/invitations/${invitationId}/decline/`);
    return response.data;
  },
};
