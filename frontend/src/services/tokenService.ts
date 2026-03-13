/**
 * Gestion du token d'accès JWT **en mémoire uniquement**.
 *
 * Le refresh token est stocké par le serveur dans un cookie HttpOnly
 * (invisible au JS). Seul l'access token est manipulé ici, en variable
 * JavaScript — il n'est jamais écrit dans localStorage.
 */

let accessToken: string | null = null;

export const tokenService = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string): void {
    accessToken = token;
  },

  clearTokens(): void {
    accessToken = null;
  },

  /**
   * Vérifie si un token JWT est expiré ou sur le point de l'être.
   * @param token - Le JWT à vérifier
   * @param bufferSeconds - Marge tampon avant l'expiration réelle (défaut : 30 s)
   */
  isTokenExpired(token: string, bufferSeconds = 30): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now() + bufferSeconds * 1000;
    } catch {
      return true;
    }
  },
};
