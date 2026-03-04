import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { tokenService } from '@/services/tokenService';
import type { User, AuthTokens } from '@/types';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: AuthTokens) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,

      setAuth: (user, tokens) => {
        tokenService.setTokens(tokens.access, tokens.refresh);
        set({ user, tokens, isAuthenticated: true });
      },

      updateUser: (user) => {
        set({ user });
      },

      logout: () => {
        tokenService.clearTokens();
        set({ user: null, tokens: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
