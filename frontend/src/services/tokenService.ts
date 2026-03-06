/**
 * Source unique de vérité pour la gestion des tokens JWT dans localStorage.
 *
 * Tous les accès à `access_token` et `refresh_token` passent par ce service,
 * évitant les accès éparpillés dans api.ts, authService.ts et authStore.ts.
 */

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

export const tokenService = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },

  setTokens(access: string, refresh: string): void {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },

  setAccessToken(access: string): void {
    localStorage.setItem(ACCESS_KEY, access);
  },

  setRefreshToken(refresh: string): void {
    localStorage.setItem(REFRESH_KEY, refresh);
  },

  clearTokens(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
