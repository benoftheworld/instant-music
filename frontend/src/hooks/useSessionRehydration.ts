/**
 * Réhydrate la session après un rechargement de page.
 *
 * Le Zustand persist-store sait que l'utilisateur était authentifié
 * (`isAuthenticated` en localStorage), mais l'access token en mémoire
 * a été perdu. Ce hook tente un silent-refresh via le cookie HttpOnly
 * pour récupérer un nouvel access token.
 */
import { useEffect, useRef } from 'react';
import { useAuthStore } from '@/store/authStore';
import { tokenService } from '@/services/tokenService';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useSessionRehydration() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);
  const attempted = useRef(false);

  useEffect(() => {
    if (!isAuthenticated || tokenService.getAccessToken() || attempted.current) return;
    attempted.current = true;

    axios
      .post(`${API_URL}/api/auth/token/refresh/`, {}, { withCredentials: true })
      .then((res) => {
        tokenService.setAccessToken(res.data.access);
      })
      .catch(() => {
        // Cookie absent ou expiré → déconnexion propre
        logout();
      });
  }, [isAuthenticated, logout]);
}
