import { useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import usePagination from '@/hooks/usePagination';
import { statsService } from '@/services/achievementService';
import { LEADERBOARD_TABS } from '@/constants/gameModes';
import { QUERY_KEYS } from '@/constants/queryKeys';
import { useAuthStore } from '@/store/authStore';
import type { LeaderboardEntry, TeamLeaderboardEntry, GameMode } from '@/types';

type LeaderboardTab = GameMode | 'general' | 'teams';

export function useLeaderboardPage() {
  const user = useAuthStore((s) => s.user);
  const [selectedMode, setSelectedMode] = useState<LeaderboardTab>('general');
  const { page, pageSize, goNext, goPrev, setPage } = usePagination(50);

  const { data, isLoading: loading, error: queryError } = useQuery({
    queryKey: QUERY_KEYS.leaderboard(selectedMode, page, pageSize),
    queryFn: async () => {
      if (selectedMode === 'teams') {
        const data = await statsService.getTeamLeaderboard(page, pageSize);
        return { players: [] as LeaderboardEntry[], teams: data.results ?? [], totalCount: data.count ?? null };
      } else if (selectedMode === 'general') {
        const data = await statsService.getLeaderboard(page, pageSize);
        return { players: data.results ?? [], teams: [] as TeamLeaderboardEntry[], totalCount: data.count ?? null };
      } else {
        const data = await statsService.getLeaderboardByMode(selectedMode, page, pageSize);
        return { players: data.results ?? [], teams: [] as TeamLeaderboardEntry[], totalCount: data.count ?? null };
      }
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });

  const players = data?.players ?? [];
  const teams = data?.teams ?? [];
  const totalCount = data?.totalCount ?? null;
  const error = queryError ? 'Impossible de charger le classement' : null;

  const handleModeChange = (mode: LeaderboardTab) => {
    setSelectedMode(mode);
    setPage(1);
  };

  const primaryTabs = LEADERBOARD_TABS.filter(
    (t) => t.value === 'general' || t.value === 'teams',
  );
  const modeTabs = LEADERBOARD_TABS.filter(
    (t) => t.value !== 'general' && t.value !== 'teams',
  );

  const subtitleMap: Record<string, string> = {
    general: 'Les meilleurs joueurs de tous les temps',
    teams: 'Les meilleures équipes de tous les temps',
    classique: 'Classement par points en mode Classique',
    rapide: 'Classement par points en mode Rapide',
    generation: 'Classement par points en mode Génération',
    paroles: 'Classement par points en mode Paroles',
    karaoke: 'Classement par points en mode Karaoké',
    mollo: 'Classement par points en mode Mollo',
  };

  return {
    user,
    selectedMode,
    page,
    pageSize,
    goNext,
    goPrev,
    players,
    teams,
    totalCount,
    loading,
    error,
    handleModeChange,
    primaryTabs,
    modeTabs,
    subtitleMap,
  };
}
