import { api } from './api';
import type { AuthResponse, LoginCredentials, RegisterData, User } from '@/types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login/', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register/', data);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/users/me/');
    return response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.patch<User>('/users/me/', data);
    return response.data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/users/change_password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  async requestPasswordReset(username: string): Promise<void> {
    await api.post('/auth/password/reset/', { username });
  },

  async confirmPasswordReset(
    uid: string,
    token: string,
    newPassword: string
  ): Promise<void> {
    await api.post('/auth/password/reset/confirm/', {
      uid,
      token,
      new_password: newPassword,
      new_password2: newPassword,
    });
  },

  async logout(): Promise<void> {
    try {
      // Le refresh token est envoyé automatiquement via cookie HttpOnly
      await api.post('/auth/logout/');
    } catch {
      // Ignorer les erreurs réseau — la déconnexion locale reste effective
    }
  },
};
