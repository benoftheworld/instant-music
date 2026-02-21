import { useState, useEffect } from 'react';
import { api, getMediaUrl } from '@/services/api';
import type { LeaderboardEntry } from '@/types';
import { Link } from 'react-router-dom';

export default function TopPlayers() {
  const [players, setPlayers] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTopPlayers();
  }, []);

  const fetchTopPlayers = async () => {
    try {
      const response = await api.get('/games/leaderboard/?limit=5');
      setPlayers(response.data);
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

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
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (players.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Aucun joueur pour le moment</p>
      </div>
    );
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
            <div className="w-12 h-12 rounded-full bg-gray-200 overflow-hidden flex-shrink-0">
              {player.avatar ? (
                <img
                  src={getMediaUrl(player.avatar)}
                  alt={player.username}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </div>

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
