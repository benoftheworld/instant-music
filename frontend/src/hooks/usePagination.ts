import { useState, useCallback } from 'react';

interface UsePaginationReturn {
  page: number;
  pageSize: number;
  totalCount: number | null;
  /** À appeler après chaque fetch pour mettre à jour le total. */
  setTotalCount: (count: number | null) => void;
  /** Nombre total de pages (null tant que totalCount est inconnu). */
  totalPages: number | null;
  hasNext: boolean;
  hasPrev: boolean;
  goNext: () => void;
  goPrev: () => void;
  /** Revient à la page 1 et réinitialise le total (ex: changement de filtre). */
  reset: () => void;
  /** Navigation directe (pour les cas où la page vient d'une query-string). */
  setPage: (page: number) => void;
}

function usePagination(pageSize = 20): UsePaginationReturn {
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState<number | null>(null);

  const totalPages =
    totalCount !== null ? Math.max(1, Math.ceil(totalCount / pageSize)) : null;

  const hasNext = totalPages !== null && page < totalPages;
  const hasPrev = page > 1;

  const goNext = useCallback(() => {
    if (hasNext) setPage((p) => p + 1);
  }, [hasNext]);

  const goPrev = useCallback(() => {
    if (hasPrev) setPage((p) => p - 1);
  }, [hasPrev]);

  const reset = useCallback(() => {
    setPage(1);
    setTotalCount(null);
  }, []);

  return {
    page,
    setPage,
    pageSize,
    totalCount,
    setTotalCount,
    totalPages,
    hasNext,
    hasPrev,
    goNext,
    goPrev,
    reset,
  };
}

export default usePagination;
