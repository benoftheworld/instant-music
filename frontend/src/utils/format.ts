/**
 * Utilitaires de formatage partagés.
 * Centralise toutes les fonctions de formatage de dates et de durées
 * pour éviter les redéfinitions locales dans les composants et pages.
 */

/**
 * Formate une date en affichage relatif français.
 * Ex. : "À l'instant", "Il y a 5 min", "Il y a 3h", "Il y a 2j", "12/03"
 */
export function formatDate(dateString: string | null): string {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins} min`;
  if (diffHours < 24) return `Il y a ${diffHours}h`;
  if (diffDays < 7) return `Il y a ${diffDays}j`;

  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
}

/**
 * Formate une date en affichage complet (date + heure).
 * Ex. : "12/03/2026 14:30"
 */
export function formatFullDate(dateString: string | null): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Formate une date via toLocaleDateString('fr-FR', options).
 * Remplace les appels inline `new Date(x).toLocaleDateString('fr-FR', ...)`.
 */
export function formatLocalDate(
  dateString: string,
  options?: Intl.DateTimeFormatOptions,
): string {
  return new Date(dateString).toLocaleDateString('fr-FR', options);
}

/**
 * Formate une durée en millisecondes au format MM:SS.
 * Ex. : 183_000 → "3:03"
 */
export function formatDuration(ms: number): string {
  if (!ms) return '--:--';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Formate une durée en secondes au format MM:SS.
 * Ex. : 183 → "3:03"
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
