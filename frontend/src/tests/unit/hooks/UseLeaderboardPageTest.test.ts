import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { createUser } from '@/tests/shared/factories';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => vi.fn() };
});

vi.mock('@/services/achievementService', () => ({
  statsService: {
    getLeaderboard: vi.fn().mockResolvedValue({ results: [], count: 0 }),
    getLeaderboardByMode: vi.fn().mockResolvedValue({ results: [], count: 0 }),
    getTeamLeaderboard: vi.fn().mockResolvedValue({ results: [], count: 0 }),
  },
}));

vi.mock('@/services/tokenService', () => ({
  tokenService: {
    setAccessToken: vi.fn(),
    clearTokens: vi.fn(),
    getAccessToken: vi.fn(),
    isTokenExpired: vi.fn(),
  },
}));

import { useLeaderboardPage } from '@/hooks/pages/useLeaderboardPage';

class UseLeaderboardPageTest {
  private createWrapper() {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(MemoryRouter, null,
        React.createElement(QueryClientProvider, { client: qc }, children)
      );
  }

  run() {
    describe('useLeaderboardPage', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        useAuthStore.setState({ user: createUser(), isAuthenticated: true });
      });

      this.testInitialState();
      this.testTabs();
    });
  }

  private testInitialState() {
    it('état initial — mode general, page 1', () => {
      const { result } = renderHook(() => useLeaderboardPage(), { wrapper: this.createWrapper() });
      expect(result.current.selectedMode).toBe('general');
      expect(result.current.page).toBe(1);
      expect(result.current.primaryTabs.length).toBeGreaterThan(0);
      expect(result.current.modeTabs.length).toBeGreaterThan(0);
    });
  }

  private testTabs() {
    it('subtitleMap contient general et teams', () => {
      const { result } = renderHook(() => useLeaderboardPage(), { wrapper: this.createWrapper() });
      expect(result.current.subtitleMap['general']).toBeTruthy();
      expect(result.current.subtitleMap['teams']).toBeTruthy();
    });
  }
}

new UseLeaderboardPageTest().run();
