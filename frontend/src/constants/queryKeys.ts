/**
 * Clés de cache centralisées pour TanStack Query.
 *
 * Avantages :
 * - Aucune faute de frappe possible (le compilateur vérifie).
 * - Invalidation cohérente depuis n'importe quel hook ou composant.
 * - Un seul endroit à modifier si un endpoint change de nom.
 *
 * Convention : chaque clé est une fonction (même sans paramètres) pour
 * garantir que TanStack Query reçoit toujours un nouveau tableau.
 */
export const QUERY_KEYS = {
  // ── Accueil ──────────────────────────────────────────────────────────────
  topPlayers: () => ['topPlayers'] as const,
  recentGames: () => ['recentGames'] as const,

  // ── Statut du site ────────────────────────────────────────────────────────
  siteStatus: () => ['site-status'] as const,

  // ── Classement ───────────────────────────────────────────────────────────
  leaderboard: (mode: string, page: number, pageSize: number) =>
    ['leaderboard', mode, page, pageSize] as const,

  // ── Social ────────────────────────────────────────────────────────────────
  friends: () => ['friends', 'all'] as const,
  teamsAll: () => ['teams', 'browse'] as const,

  // ── Profil ────────────────────────────────────────────────────────────────
  profileAchievements: () => ['profile', 'achievements'] as const,
  profileStats: () => ['profile', 'stats'] as const,

  // ── Boutique (toute la famille pour permettre l'invalidation en bloc) ─────
  shop: () => ['shop'] as const,
  shopItems: () => ['shop', 'items'] as const,
  shopSummary: () => ['shop', 'summary'] as const,
  shopInventory: () => ['shop', 'inventory'] as const,
};
