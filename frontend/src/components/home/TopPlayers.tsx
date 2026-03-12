import { useQuery } from '@tanstack/react-query';
import { gameService } from '@/services/gameService';
import { Avatar, LoadingState, EmptyState } from '@/components/ui';
import { QUERY_KEYS } from '@/constants/queryKeys';
import type { LeaderboardEntry } from '@/types';
import { Link } from 'react-router-dom';

export default function TopPlayers() {
  const { data: players = [], isLoading: loading } = useQuery<LeaderboardEntry[]>({
    queryKey: QUERY_KEYS.topPlayers(),
    queryFn: () => gameService.getTopPlayers(5),
    staleTime: 60_000,
  });

  const getRankColor = (index: number) => {
    switch (index) {
      case 0:
        return 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white';
      case 1:
        return 'bg-gradient-to-br from-gray-400 to-gray-600 text-white';
      case 2:
        return 'bg-gradient-to-br from-orange-600 to-orange-800 text-white';
      default:
        return 'bg-gray-200 text-gray-700';
    }
  };

  const getRankIcon = (index: number) => {
    switch (index) {
      case 0:
        return '🥇';
      case 1:
        return '🥈';
      case 2:
        return '🥉';
      default:
        return `${index + 1}`;
    }
  };

  if (loading) {
    return <LoadingState />;
  }

  if (players.length === 0) {
    return <EmptyState title="Aucun joueur pour le moment" />;
  }

  return (
    <div className="space-y-3">
      {players.map((player, index) => (
        <div
          key={player.user_id}
          className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center space-x-4">
            {/* Rank Badge */}
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold flex-shrink-0 ${getRankColor(
                index
              )}`}
            >
              {index < 3 ? (
                <span className="text-xl">{getRankIcon(index)}</span>
              ) : (
                <span className="text-sm">{index + 1}</span>
              )}
            </div>

            {/* Avatar */}
            <Avatar username={player.username} src={player.avatar} size="md" className="flex-shrink-0" />

            {/* Player Info */}
            <div className="flex-1 min-w-0">
              <p className="font-bold text-sm truncate">{player.username}</p>
              <div className="flex items-center space-x-3 mt-1 text-xs text-gray-600">
                <span>{player.total_games} parties</span>
                <span className="text-green-600 font-medium">{player.total_wins} victoires</span>
              </div>
            </div>

            {/* Points */}
            <div className="text-right">
              <p className="text-lg font-bold text-primary-600">{player.total_points}</p>
              <p className="text-xs text-gray-500">points</p>
            </div>
          </div>
        </div>
      ))}
      <div className="text-center mt-2">
        <Link
          to="/leaderboard"
          className="text-sm text-primary-600 hover:underline font-medium"
        >
          Voir tout le classement
        </Link>
      </div>
    </div>
  );
}
