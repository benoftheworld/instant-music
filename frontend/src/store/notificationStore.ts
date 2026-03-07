import { create } from 'zustand';
import type { GameInvitation } from '@/types';

interface NotificationState {
  invitations: GameInvitation[];
  // Add a new invitation (from WS push)
  addInvitation: (invitation: GameInvitation) => void;
  // Remove an invitation (accepted, declined, or cancelled)
  removeInvitation: (invitationId: string) => void;
  // Replace all invitations (initial load from API)
  setInvitations: (invitations: GameInvitation[]) => void;
  // Dismiss all
  clearInvitations: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  invitations: [],

  addInvitation: (invitation) =>
    set((state) => {
      // Avoid duplicates
      const exists = state.invitations.some((i) => i.id === invitation.id);
      if (exists) return state;
      return { invitations: [invitation, ...state.invitations] };
    }),

  removeInvitation: (invitationId) =>
    set((state) => ({
      invitations: state.invitations.filter((i) => i.id !== invitationId),
    })),

  setInvitations: (invitations) => set({ invitations }),

  clearInvitations: () => set({ invitations: [] }),
}));
