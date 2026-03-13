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
import { refreshAccessToken } from '@/services/api';

export function useSessionRehydration() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);
  const attempted = useRef(false);

  useEffect(() => {
    if (!isAuthenticated || tokenService.getAccessToken() || attempted.current) return;
    attempted.current = true;

    // Utilise la fonction partagée (avec verrou isRefreshing) pour éviter
    // la race condition avec les intercepteurs axios lors du rechargement.
    refreshAccessToken().catch(() => {
      // Cookie absent ou expiré → déconnexion propre
      logout();
    });
  }, [isAuthenticated, logout]);
}
