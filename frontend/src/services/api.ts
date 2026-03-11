import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from './tokenService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Queue pour éviter plusieurs appels refresh simultanés (race condition).
// Quand un refresh est déjà en cours, les requêtes suivantes attendent
// sa résolution avant d'être rejouées avec le nouveau token.
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token as string);
    }
  });
  failedQueue = [];
}

/**
 * Rafraîchit le token d'accès de façon centralisée.
 * Si un refresh est déjà en cours, met en file d'attente et attend le résultat.
 * En cas d'échec, déconnecte l'utilisateur et redirige vers /login.
 */
async function refreshAccessToken(): Promise<string> {
  if (isRefreshing) {
    return new Promise<string>((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;
  try {
    const refreshToken = tokenService.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token available');

    const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
      refresh: refreshToken,
    });
    const { access, refresh: newRefresh } = response.data;
    tokenService.setAccessToken(access);
    if (newRefresh) tokenService.setRefreshToken(newRefresh);

    processQueue(null, access);
    return access;
  } catch (error) {
    processQueue(error);
    useAuthStore.getState().logout();
    window.location.href = '/login';
    throw error;
  } finally {
    isRefreshing = false;
  }
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Intercepteur de requête : refresh proactif si le token est expiré ou
    // sur le point de l'être (marge de 30 s). Évite que le backend reçoive
    // des requêtes avec un token déjà invalide et logue des 401.
    this.api.interceptors.request.use(
      async (config) => {
        const token = tokenService.getAccessToken();
        if (token) {
          if (tokenService.isTokenExpired(token)) {
            const freshToken = await refreshAccessToken();
            config.headers.Authorization = `Bearer ${freshToken}`;
          } else {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Intercepteur de réponse : filet de sécurité pour les 401 résiduels
    // (token expiré entre l'envoi et la réception, ou endpoint hors axios).
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            const token = await refreshAccessToken();
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return this.api(originalRequest);
          } catch (refreshError) {
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  getApi() {
    return this.api;
  }
}

export const apiService = new ApiService();
export const api = apiService.getApi();

/**
 * Get full URL for media files (avatars, etc.)
 */
export const getMediaUrl = (path: string | undefined | null): string | undefined => {
  if (!path) return undefined;

  // If already an absolute URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  // Protocol-relative URL (e.g. //cdn.example.com/img.png)
  if (path.startsWith('//')) {
    return `${window.location.protocol}${path}`;
  }

  // Root-relative or relative path → always prepend API_URL (backend origin)
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${cleanPath}`;
};
