import { create } from 'zustand';
import type { GameInvitation, UserMinimal } from '@/types';

export interface PendingFriendRequest {
  id: number;
  from_user: UserMinimal;
  created_at: string;
}

export interface SocialNotification {
  id: string;
  type: 'friend_request_accepted' | 'team_join_request' | 'team_join_approved';
  message: string;
  link?: string;
  created_at: string;
}

interface NotificationState {
  invitations: GameInvitation[];
  friendRequests: PendingFriendRequest[];
  socialNotifications: SocialNotification[];

  // Game invitations
  addInvitation: (invitation: GameInvitation) => void;
  removeInvitation: (invitationId: string) => void;
  setInvitations: (invitations: GameInvitation[]) => void;

  // Friend requests
  addFriendRequest: (req: PendingFriendRequest) => void;
  removeFriendRequest: (friendshipId: number) => void;
  setFriendRequests: (reqs: PendingFriendRequest[]) => void;

  // Informational social notifications
  addSocialNotification: (notif: SocialNotification) => void;
  removeSocialNotification: (id: string) => void;

  // Clear all on logout
  clearInvitations: () => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  invitations: [],
  friendRequests: [],
  socialNotifications: [],

  addInvitation: (invitation) =>
    set((state) => {
      const exists = state.invitations.some((i) => i.id === invitation.id);
      if (exists) return state;
      return { invitations: [invitation, ...state.invitations] };
    }),

  removeInvitation: (invitationId) =>
    set((state) => ({
      invitations: state.invitations.filter((i) => i.id !== invitationId),
    })),

  setInvitations: (invitations) => set({ invitations }),

  addFriendRequest: (req) =>
    set((state) => {
      const exists = state.friendRequests.some((r) => r.id === req.id);
      if (exists) return state;
      return { friendRequests: [req, ...state.friendRequests] };
    }),

  removeFriendRequest: (friendshipId) =>
    set((state) => ({
      friendRequests: state.friendRequests.filter((r) => r.id !== friendshipId),
    })),

  setFriendRequests: (reqs) => set({ friendRequests: reqs }),

  addSocialNotification: (notif) =>
    set((state) => {
      const exists = state.socialNotifications.some((n) => n.id === notif.id);
      if (exists) return state;
      return { socialNotifications: [notif, ...state.socialNotifications] };
    }),

  removeSocialNotification: (id) =>
    set((state) => ({
      socialNotifications: state.socialNotifications.filter((n) => n.id !== id),
    })),

  clearInvitations: () => set({ invitations: [] }),

  clearAll: () => set({ invitations: [], friendRequests: [], socialNotifications: [] }),
}));
