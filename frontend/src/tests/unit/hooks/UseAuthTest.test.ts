import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { createUser } from '@/tests/shared/factories';
import type { AuthResponse, User } from '@/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
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

import { useLogin, useRegister, useLogout } from '@/hooks/useAuth';

class UseAuthTest {
  private createWrapper() {
    const qc = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(MemoryRouter, null,
        React.createElement(QueryClientProvider, { client: qc }, children)
      );
  }

  run() {
    describe('useAuth hooks', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        useAuthStore.setState({ user: null, isAuthenticated: false });
      });

      this.testLoginSuccess();
      this.testRegisterSuccess();
      this.testLogout();
    });
  }

  private testLoginSuccess() {
    it('useLogin — succès : stocke auth et navigue vers /', async () => {
      const { authService } = await import('@/services/authService');
      const user = createUser();
      const response: AuthResponse = { user, tokens: { access: 'a', refresh: 'r' } };
      (authService.login as ReturnType<typeof vi.fn>).mockResolvedValue(response);

      const { result } = renderHook(() => useLogin(), { wrapper: this.createWrapper() });
      await act(async () => {
        result.current.mutate({ email: 'a@b.c', password: 'pass' });
      });

      await vi.waitFor(() => {
        expect(useAuthStore.getState().isAuthenticated).toBe(true);
      });
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  }

  private testRegisterSuccess() {
    it('useRegister — succès : stocke auth et navigue vers /', async () => {
      const { authService } = await import('@/services/authService');
      const user = createUser();
      const response: AuthResponse = { user, tokens: { access: 'a', refresh: 'r' } };
      (authService.register as ReturnType<typeof vi.fn>).mockResolvedValue(response);

      const { result } = renderHook(() => useRegister(), { wrapper: this.createWrapper() });
      await act(async () => {
        result.current.mutate({ username: 'u', email: 'e@f.g', password: 'pass' });
      });

      await vi.waitFor(() => {
        expect(useAuthStore.getState().isAuthenticated).toBe(true);
      });
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  }

  private testLogout() {
    it('useLogout — appelle authService.logout, vide le store, navigue vers /login', async () => {
      const { authService } = await import('@/services/authService');
      useAuthStore.setState({ user: createUser(), isAuthenticated: true });

      const { result } = renderHook(() => useLogout(), { wrapper: this.createWrapper() });
      await act(async () => {
        await result.current();
      });

      expect(authService.logout).toHaveBeenCalled();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  }
}

new UseAuthTest().run();
