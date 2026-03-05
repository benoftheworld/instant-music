import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore } from '@/store/notificationStore';

const mockInvitation = (id: string) => ({
  id,
  game: { id: 'game-1', room_code: 'ABC123', name: 'Test', host_username: 'host' },
  sender: { id: 'user-1', username: 'host' },
  recipient: { id: 'user-2', username: 'player' },
  status: 'pending' as const,
  created_at: '2024-01-01T00:00:00Z',
  expires_at: '2024-01-01T01:00:00Z',
});

describe('notificationStore', () => {
  beforeEach(() => {
    useNotificationStore.setState({ invitations: [] });
  });

  it('etat initial sans invitations', () => {
    expect(useNotificationStore.getState().invitations).toEqual([]);
  });

  it('addInvitation ajoute une invitation', () => {
    useNotificationStore.getState().addInvitation(mockInvitation('inv-1') as any);
    expect(useNotificationStore.getState().invitations).toHaveLength(1);
  });

  it('addInvitation ne duplique pas', () => {
    const inv = mockInvitation('inv-1') as any;
    useNotificationStore.getState().addInvitation(inv);
    useNotificationStore.getState().addInvitation(inv);
    expect(useNotificationStore.getState().invitations).toHaveLength(1);
  });

  it('removeInvitation retire une invitation par id', () => {
    useNotificationStore.getState().addInvitation(mockInvitation('inv-1') as any);
    useNotificationStore.getState().addInvitation(mockInvitation('inv-2') as any);
    useNotificationStore.getState().removeInvitation('inv-1');
    expect(useNotificationStore.getState().invitations).toHaveLength(1);
    expect(useNotificationStore.getState().invitations[0].id).toBe('inv-2');
  });

  it('setInvitations remplace la liste', () => {
    useNotificationStore.getState().addInvitation(mockInvitation('inv-1') as any);
    useNotificationStore
      .getState()
      .setInvitations([mockInvitation('inv-3') as any, mockInvitation('inv-4') as any]);
    expect(useNotificationStore.getState().invitations).toHaveLength(2);
  });

  it('clearInvitations vide la liste', () => {
    useNotificationStore.getState().addInvitation(mockInvitation('inv-1') as any);
    useNotificationStore.getState().clearInvitations();
    expect(useNotificationStore.getState().invitations).toEqual([]);
  });
});
