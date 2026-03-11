import { useState, useCallback } from 'react';

/**
 * Synchronise un état React avec une clé localStorage.
 *
 * - Lecture initiale : tente un JSON.parse, puis accepte la valeur brute en
 *   fallback (rétrocompatibilité avec les entrées non-JSON existantes).
 * - Écriture : stocke toujours en JSON. Passer `null` supprime la clé.
 * - Les erreurs d'accès au storage (mode privé / quota) sont ignorées
 *   silencieusement ; l'état React reste cohérent.
 */
function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      if (item === null) return initialValue;
      try {
        return JSON.parse(item) as T;
      } catch {
        // Legacy: value was stored as a raw string (not JSON-encoded)
        return item as unknown as T;
      }
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const next =
          typeof value === 'function' ? (value as (prev: T) => T)(prev) : value;
        try {
          if (next === null || next === undefined) {
            localStorage.removeItem(key);
          } else {
            localStorage.setItem(key, JSON.stringify(next));
          }
        } catch {
          // Ignore storage errors (private mode, quota exceeded…)
        }
        return next;
      });
    },
    [key],
  );

  return [storedValue, setValue];
}

export default useLocalStorage;
