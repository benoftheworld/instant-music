import type { GamePlayer } from '@/types';

/**
 * Fusionne une liste de joueurs mis à jour dans la liste de joueurs existante.
 *
 * @param existing - Les joueurs actuels
 * @param updated - Les joueurs avec des données mises à jour (scores, streaks…)
 * @param preserveAvatar - Si vrai, conserve l'avatar existant si le nouveau est absent (défaut: true)
 */
export function mergeUpdatedPlayers(
  existing: GamePlayer[],
  updated: Partial<GamePlayer>[],
  preserveAvatar = true,
): GamePlayer[] {
  const updatedMap: Record<string | number, Partial<GamePlayer>> = {};
  for (const p of updated) {
    if (p.id !== undefined) updatedMap[p.id] = p;
  }
  return existing.map((p) => {
    const u = updatedMap[p.id];
    if (!u) return p;
    const merged = { ...p, ...u };
    if (preserveAvatar) {
      merged.avatar = u.avatar ?? p.avatar;
    }
    return merged as GamePlayer;
  });
}
