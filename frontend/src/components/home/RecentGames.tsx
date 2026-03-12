import { useQuery } from '@tanstack/react-query';
import { getMediaUrl } from '@/services/api';
import { gameService } from '@/services/gameService';
import { getModeIcon } from '@/constants/gameModes';
import { LoadingState, EmptyState } from '@/components/ui';
import { formatDate } from '@/utils/format';
import { QUERY_KEYS } from '@/constants/queryKeys';
import type { GameHistory } from '@/types';
import { Link } from 'react-router-dom';

export default function RecentGames() {
  const { data: games = [], isLoading: loading } = useQuery<GameHistory[]>({
    queryKey: QUERY_KEYS.recentGames(),
    queryFn: () => gameService.getRecentGames(5),
    staleTime: 30_000,
  });

  if (loading) {
    return <LoadingState />;
  }

  if (games.length === 0) {
    return <EmptyState title="Aucune partie récente" />;
  }

  return (
    <div className="space-y-3">
      {games.map((game) => (
        <div key={game.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <span className="text-2xl">{getModeIcon(game.mode)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h4 className="font-bold text-sm truncate">{game.mode_display}</h4>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {game.player_count} joueurs
                  </span>
                </div>
                {game.winner && (
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-gray-500">Vainqueur:</span>
                    <div className="flex items-center space-x-1">
                      {game.winner.avatar ? (
                        <img
                          src={getMediaUrl(game.winner.avatar)}
                          alt={game.winner.username}
                          className="w-4 h-4 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-yellow-400 flex items-center justify-center">
                          <span className="text-white text-[8px]">👑</span>
                        </div>
                      )}
                      <span className="text-xs font-medium truncate">{game.winner.username}</span>
                      <span className="text-xs text-primary-600">({game.winner_score} pts)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="text-right ml-4">
              <p className="text-xs text-gray-500">{formatDate(game.finished_at)}</p>
            </div>
          </div>
        </div>
      ))}

      <div className="text-center pt-2">
        <Link to="/history" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          Voir tout l'historique →
        </Link>
      </div>
    </div>
  );
}
