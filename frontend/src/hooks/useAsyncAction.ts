import { useState, useCallback } from 'react';

interface UseAsyncActionReturn {
  loading: boolean;
  error: string | null;
  /** Permet de poser un message d'erreur manuellement depuis l'appelant. */
  setError: (error: string | null) => void;
  clearError: () => void;
  /**
   * Exécute `action` en gérant automatiquement le cycle loading/error :
   * - Passe loading à `true` et réinitialise l'erreur avant l'appel.
   * - En cas d'exception, appelle `onError` (si fourni) pour extraire le
   *   message, sinon utilise `err.message` ou un texte générique.
   * - Repasse toujours loading à `false` dans le bloc finally.
   *
   * Astuce : si l'action gère elle-même l'erreur (catch interne + setError)
   * sans relancer, le catch de `run` n'est pas exécuté.
   */
  run: <T>(
    action: () => Promise<T>,
    onError?: (err: unknown) => string,
  ) => Promise<T | undefined>;
}

function useAsyncAction(): UseAsyncActionReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const run = useCallback(
    async <T>(
      action: () => Promise<T>,
      onError?: (err: unknown) => string,
    ): Promise<T | undefined> => {
      setLoading(true);
      setError(null);
      try {
        return await action();
      } catch (err) {
        const message = onError
          ? onError(err)
          : err instanceof Error
          ? err.message
          : 'Une erreur inattendue est survenue.';
        setError(message);
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return { loading, error, setError, clearError, run };
}

export default useAsyncAction;
