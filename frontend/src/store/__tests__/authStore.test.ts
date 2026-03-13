import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from '@/services/tokenService';

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  is_staff: false,
  total_games_played: 5,
  total_wins: 2,
  total_points: 100,
  coins_balance: 50,
  win_rate: 40.0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockAccessToken = 'access-token-123';

describe('authStore', () => {
  beforeEach(() => {
    tokenService.clearTokens();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
    });
  });

  it('etat initial non authentifie', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('setAuth stocke user et authentifie', () => {
    useAuthStore.getState().setAuth(mockUser, mockAccessToken);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
  });

  it('setAuth ecrit le access token en memoire', () => {
    useAuthStore.getState().setAuth(mockUser, mockAccessToken);

    expect(tokenService.getAccessToken()).toBe('access-token-123');
  });

  it('updateUser met a jour le user sans toucher au token', () => {
    useAuthStore.getState().setAuth(mockUser, mockAccessToken);

    const updatedUser = { ...mockUser, id: 1, username: 'newname' };
    useAuthStore.getState().updateUser(updatedUser);

    const state = useAuthStore.getState();
    expect(state.user?.username).toBe('newname');
    expect(tokenService.getAccessToken()).toBe('access-token-123');
    expect(state.isAuthenticated).toBe(true);
  });

  it('logout reinitialise tout', () => {
    useAuthStore.getState().setAuth(mockUser, mockAccessToken);
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('logout supprime le access token de la memoire', () => {
    useAuthStore.getState().setAuth(mockUser, mockAccessToken);
    useAuthStore.getState().logout();

    expect(tokenService.getAccessToken()).toBeNull();
  });
});
