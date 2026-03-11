import { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import type { GameHistory } from '@/types';
import useAsyncAction from '@/hooks/useAsyncAction';
import usePagination from '@/hooks/usePagination';

export function useGameHistoryPage() {
  const [games, setGames] = useState<GameHistory[]>([]);
  const [selectedMode, setSelectedMode] = useState<string | null>(null);

  const { loading, error, run } = useAsyncAction();
  const { page, pageSize, totalCount, setTotalCount, hasNext, hasPrev, goNext, goPrev, reset } =
    usePagination(20);

  const fetchGameHistory = useCallback(
    (p: number, mode?: string) =>
      run(async () => {
        const params: Record<string, unknown> = { page: p, page_size: pageSize };
        if (mode) params.mode = mode;
        const response = await api.get('/games/history/', { params });
        const data = response.data;
        const results = Array.isArray(data) ? data : data.results ?? [];
        setGames(results);
        setTotalCount(!Array.isArray(data) ? (data.count ?? null) : null);
      }, () => "Impossible de charger l'historique des parties"),
    [run, pageSize, setTotalCount],
  );

  useEffect(() => {
    reset();
    fetchGameHistory(1, selectedMode ?? undefined);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMode]);

  useEffect(() => {
    if (page !== 1) fetchGameHistory(page, selectedMode ?? undefined);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handlePrev = () => { goPrev(); };
  const handleNext = () => { goNext(); };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return {
    games,
    selectedMode,
    setSelectedMode,
    loading,
    error,
    page,
    pageSize,
    totalCount,
    hasNext,
    hasPrev,
    handlePrev,
    handleNext,
    formatDate,
  };
}
