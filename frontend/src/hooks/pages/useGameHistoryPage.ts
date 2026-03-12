import { useState, useEffect, useCallback } from 'react';
import { gameService } from '@/services/gameService';
import { formatFullDate } from '@/utils/format';
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
        const { results, count } = await gameService.getGameHistory(p, pageSize, mode);
        setGames(results);
        setTotalCount(count ?? null);
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
    formatDate: formatFullDate,
  };
}
