import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from '@/services/tokenService';
import { createUser } from '@/tests/shared/factories';

vi.mock('@/services/tokenService', () => ({
  tokenService: {
    setAccessToken: vi.fn(),
    clearTokens: vi.fn(),
    getAccessToken: vi.fn(),
    isTokenExpired: vi.fn(),
  },
}));

class AuthStoreTest {
  run() {
    describe('AuthStore', () => {
      beforeEach(() => {
        useAuthStore.setState({ user: null, isAuthenticated: false });
        vi.clearAllMocks();
      });

      this.testInitialState();
      this.testSetAuth();
      this.testUpdateUser();
      this.testLogout();
    });
  }

  private testInitialState() {
    it('état initial — non authentifié, user null', () => {
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  }

  private testSetAuth() {
    it('setAuth — définit user et stocke le token', () => {
      const user = createUser();
      useAuthStore.getState().setAuth(user, 'access-token-123');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(user);
      expect(state.isAuthenticated).toBe(true);
      expect(tokenService.setAccessToken).toHaveBeenCalledWith('access-token-123');
    });
  }

  private testUpdateUser() {
    it('updateUser — met à jour le profil sans toucher le token', () => {
      const user = createUser();
      useAuthStore.getState().setAuth(user, 'token');
      vi.clearAllMocks();

      const updated = { ...user, username: 'new-name' };
      useAuthStore.getState().updateUser(updated);

      const state = useAuthStore.getState();
      expect(state.user?.username).toBe('new-name');
      expect(state.isAuthenticated).toBe(true);
      expect(tokenService.setAccessToken).not.toHaveBeenCalled();
    });
  }

  private testLogout() {
    it('logout — efface user, tokens, et isAuthenticated', () => {
      const user = createUser();
      useAuthStore.getState().setAuth(user, 'token');
      vi.clearAllMocks();

      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(tokenService.clearTokens).toHaveBeenCalled();
    });
  }
}

new AuthStoreTest().run();
