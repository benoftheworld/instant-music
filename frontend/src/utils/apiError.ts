import axios from 'axios';

/**
 * Extrait un message d'erreur lisible depuis une erreur Axios ou inconnue.
 */
export function getApiErrorMessage(err: unknown, fallback = 'Une erreur est survenue.'): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (typeof data === 'string') return data;
    if (data?.error) return data.error;
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;
    // Erreurs de validation Django DRF : { "field": ["msg", ...] }
    if (typeof data === 'object' && data !== null) {
      const firstField = Object.values(data).find(Array.isArray);
      if (firstField && firstField.length > 0) return String(firstField[0]);
    }
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
