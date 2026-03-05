import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from '@/services/tokenService';

const mockUser = {
  id: 'user-uuid-1',
  username: 'testuser',
  email: 'test@example.com',
  avatar: null,
  is_staff: false,
  total_games_played: 5,
  total_wins: 2,
  total_points: 100,
  coins_balance: 50,
  win_rate: 40.0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockTokens = {
  access: 'access-token-123',
  refresh: 'refresh-token-456',
};

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
    });
  });

  it('etat initial non authentifie', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.tokens).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('setAuth stocke user + tokens et authentifie', () => {
    useAuthStore.getState().setAuth(mockUser, mockTokens);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.tokens).toEqual(mockTokens);
    expect(state.isAuthenticated).toBe(true);
  });

  it('setAuth ecrit les tokens dans localStorage', () => {
    useAuthStore.getState().setAuth(mockUser, mockTokens);

    expect(tokenService.getAccessToken()).toBe('access-token-123');
    expect(tokenService.getRefreshToken()).toBe('refresh-token-456');
  });

  it('updateUser met a jour le user sans toucher aux tokens', () => {
    useAuthStore.getState().setAuth(mockUser, mockTokens);

    const updatedUser = { ...mockUser, username: 'newname' };
    useAuthStore.getState().updateUser(updatedUser);

    const state = useAuthStore.getState();
    expect(state.user?.username).toBe('newname');
    expect(state.tokens).toEqual(mockTokens);
    expect(state.isAuthenticated).toBe(true);
  });

  it('logout reinitialise tout', () => {
    useAuthStore.getState().setAuth(mockUser, mockTokens);
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.tokens).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('logout supprime les tokens du localStorage', () => {
    useAuthStore.getState().setAuth(mockUser, mockTokens);
    useAuthStore.getState().logout();

    expect(tokenService.getAccessToken()).toBeNull();
    expect(tokenService.getRefreshToken()).toBeNull();
  });
});
