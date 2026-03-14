import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore } from '@/store/notificationStore';
import type { PendingFriendRequest, SocialNotification } from '@/store/notificationStore';
import type { GameInvitation } from '@/types';

const makeInvitation = (overrides: Partial<GameInvitation> = {}): GameInvitation => ({
  id: 'inv-1',
  game: 'G123',
  game_code: 'ABCD',
  from_user: { id: 1, username: 'alice', avatar: null },
  status: 'pending',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

const makeFriendRequest = (overrides: Partial<PendingFriendRequest> = {}): PendingFriendRequest => ({
  id: 1,
  from_user: { id: 2, username: 'bob', avatar: null },
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

const makeSocialNotif = (overrides: Partial<SocialNotification> = {}): SocialNotification => ({
  id: 'sn-1',
  type: 'friend_request_accepted',
  message: 'Alice a accepté votre demande',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

class NotificationStoreTest {
  run() {
    describe('NotificationStore', () => {
      beforeEach(() => {
        useNotificationStore.setState({
          invitations: [],
          friendRequests: [],
          socialNotifications: [],
        });
      });

      this.testInitialState();
      this.testInvitations();
      this.testFriendRequests();
      this.testSocialNotifications();
      this.testClearAll();
    });
  }

  private testInitialState() {
    it('état initial — listes vides', () => {
      const state = useNotificationStore.getState();
      expect(state.invitations).toEqual([]);
      expect(state.friendRequests).toEqual([]);
      expect(state.socialNotifications).toEqual([]);
    });
  }

  private testInvitations() {
    describe('Invitations de jeu', () => {
      it('addInvitation — ajoute en tête', () => {
        const inv = makeInvitation();
        useNotificationStore.getState().addInvitation(inv);
        expect(useNotificationStore.getState().invitations).toHaveLength(1);
        expect(useNotificationStore.getState().invitations[0]).toEqual(inv);
      });

      it('addInvitation — ignore les doublons', () => {
        const inv = makeInvitation();
        useNotificationStore.getState().addInvitation(inv);
        useNotificationStore.getState().addInvitation(inv);
        expect(useNotificationStore.getState().invitations).toHaveLength(1);
      });

      it('removeInvitation — supprime par id', () => {
        const inv = makeInvitation();
        useNotificationStore.getState().addInvitation(inv);
        useNotificationStore.getState().removeInvitation('inv-1');
        expect(useNotificationStore.getState().invitations).toHaveLength(0);
      });

      it('setInvitations — remplace toute la liste', () => {
        const list = [makeInvitation({ id: 'a' }), makeInvitation({ id: 'b' })];
        useNotificationStore.getState().setInvitations(list);
        expect(useNotificationStore.getState().invitations).toHaveLength(2);
      });

      it('clearInvitations — vide seulement les invitations', () => {
        useNotificationStore.getState().addInvitation(makeInvitation());
        useNotificationStore.getState().addFriendRequest(makeFriendRequest());
        useNotificationStore.getState().clearInvitations();
        expect(useNotificationStore.getState().invitations).toHaveLength(0);
        expect(useNotificationStore.getState().friendRequests).toHaveLength(1);
      });
    });
  }

  private testFriendRequests() {
    describe('Demandes d\'amitié', () => {
      it('addFriendRequest — ajoute en tête', () => {
        const req = makeFriendRequest();
        useNotificationStore.getState().addFriendRequest(req);
        expect(useNotificationStore.getState().friendRequests).toHaveLength(1);
      });

      it('addFriendRequest — ignore les doublons', () => {
        const req = makeFriendRequest();
        useNotificationStore.getState().addFriendRequest(req);
        useNotificationStore.getState().addFriendRequest(req);
        expect(useNotificationStore.getState().friendRequests).toHaveLength(1);
      });

      it('removeFriendRequest — supprime par id', () => {
        useNotificationStore.getState().addFriendRequest(makeFriendRequest({ id: 10 }));
        useNotificationStore.getState().removeFriendRequest(10);
        expect(useNotificationStore.getState().friendRequests).toHaveLength(0);
      });

      it('setFriendRequests — remplace toute la liste', () => {
        useNotificationStore.getState().setFriendRequests([
          makeFriendRequest({ id: 1 }),
          makeFriendRequest({ id: 2 }),
        ]);
        expect(useNotificationStore.getState().friendRequests).toHaveLength(2);
      });
    });
  }

  private testSocialNotifications() {
    describe('Notifications sociales', () => {
      it('addSocialNotification — ajoute en tête', () => {
        const notif = makeSocialNotif();
        useNotificationStore.getState().addSocialNotification(notif);
        expect(useNotificationStore.getState().socialNotifications).toHaveLength(1);
      });

      it('addSocialNotification — ignore les doublons', () => {
        const notif = makeSocialNotif();
        useNotificationStore.getState().addSocialNotification(notif);
        useNotificationStore.getState().addSocialNotification(notif);
        expect(useNotificationStore.getState().socialNotifications).toHaveLength(1);
      });

      it('removeSocialNotification — supprime par id', () => {
        useNotificationStore.getState().addSocialNotification(makeSocialNotif({ id: 'x' }));
        useNotificationStore.getState().removeSocialNotification('x');
        expect(useNotificationStore.getState().socialNotifications).toHaveLength(0);
      });
    });
  }

  private testClearAll() {
    it('clearAll — vide toutes les collections', () => {
      useNotificationStore.getState().addInvitation(makeInvitation());
      useNotificationStore.getState().addFriendRequest(makeFriendRequest());
      useNotificationStore.getState().addSocialNotification(makeSocialNotif());
      useNotificationStore.getState().clearAll();

      const state = useNotificationStore.getState();
      expect(state.invitations).toHaveLength(0);
      expect(state.friendRequests).toHaveLength(0);
      expect(state.socialNotifications).toHaveLength(0);
    });
  }
}

new NotificationStoreTest().run();
