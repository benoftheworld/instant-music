/**
 * Formate une réponse qui peut être du JSON (legacy) ou du texte brut pour l'affichage.
 *
 * Gère le cas où la réponse est un objet JSON avec des champs `artist` et/ou `title`,
 * hérité d'un ancien format de réponse.
 */
export function formatAnswer(answer: string): string {
  try {
    const parsed = JSON.parse(answer);
    if (parsed && typeof parsed === 'object') {
      const parts: string[] = [];
      if (parsed.artist) parts.push(parsed.artist);
      if (parsed.title) parts.push(parsed.title);
      if (parts.length) return parts.join(' - ');
    }
  } catch {
    /* not JSON, use as-is */
  }
  return answer;
}
