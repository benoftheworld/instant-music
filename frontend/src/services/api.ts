import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from './tokenService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Queue pour éviter plusieurs appels refresh simultanés (race condition).
// Quand un refresh est déjà en cours, les requêtes 401 suivantes attendent
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

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = tokenService.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          // Un refresh est déjà en cours : on met la requête en file d'attente
          // pour éviter plusieurs appels concurrents à /token/refresh/.
          if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
              failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return this.api(originalRequest);
              })
              .catch((err) => Promise.reject(err));
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            const refreshToken = tokenService.getRefreshToken();
            if (refreshToken) {
              const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
                refresh: refreshToken,
              });

              const { access, refresh: newRefresh } = response.data;
              tokenService.setAccessToken(access);
              if (newRefresh) {
                tokenService.setRefreshToken(newRefresh);
              }

              processQueue(null, access);
              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Le refresh a échoué — on rejette toutes les requêtes en attente
            // puis on vide le store et on redirige vers /login.
            processQueue(refreshError);
            useAuthStore.getState().logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
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
