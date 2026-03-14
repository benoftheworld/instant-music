import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useSessionRehydration } from '@/hooks/useSessionRehydration';
import { useAuthStore } from '@/store/authStore';

vi.mock('@/services/tokenService', () => ({
  tokenService: {
    getAccessToken: vi.fn(() => null),
    setAccessToken: vi.fn(),
    clearTokens: vi.fn(),
    isTokenExpired: vi.fn(),
  },
}));

vi.mock('@/services/api', () => ({
  refreshAccessToken: vi.fn().mockResolvedValue(undefined),
}));

class UseSessionRehydrationTest {
  run() {
    describe('useSessionRehydration', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        useAuthStore.setState({ user: null, isAuthenticated: false });
      });

      this.testNoRefreshWhenNotAuthenticated();
      this.testRefreshWhenAuthenticatedNoToken();
      this.testNoRefreshWhenTokenPresent();
    });
  }

  private testNoRefreshWhenNotAuthenticated() {
    it('ne tente pas de refresh si non authentifié', async () => {
      const { refreshAccessToken } = await import('@/services/api');
      renderHook(() => useSessionRehydration());
      expect(refreshAccessToken).not.toHaveBeenCalled();
    });
  }

  private testRefreshWhenAuthenticatedNoToken() {
    it('tente un refresh si authentifié sans token mémoire', async () => {
      const { refreshAccessToken } = await import('@/services/api');
      useAuthStore.setState({ isAuthenticated: true, user: { id: 1, username: 'x' } as any });
      renderHook(() => useSessionRehydration());
      expect(refreshAccessToken).toHaveBeenCalled();
    });
  }

  private testNoRefreshWhenTokenPresent() {
    it('ne tente pas de refresh si token déjà présent', async () => {
      const { tokenService } = await import('@/services/tokenService');
      (tokenService.getAccessToken as ReturnType<typeof vi.fn>).mockReturnValue('tok');
      const { refreshAccessToken } = await import('@/services/api');
      useAuthStore.setState({ isAuthenticated: true, user: { id: 1, username: 'x' } as any });
      renderHook(() => useSessionRehydration());
      expect(refreshAccessToken).not.toHaveBeenCalled();
    });
  }
}

new UseSessionRehydrationTest().run();
