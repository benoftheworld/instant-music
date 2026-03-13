import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { tokenService } from '@/services/tokenService';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setAuth: (user, accessToken) => {
        tokenService.setAccessToken(accessToken);
        set({ user, isAuthenticated: true });
      },

      updateUser: (user) => {
        set({ user });
      },

      logout: () => {
        tokenService.clearTokens();
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
