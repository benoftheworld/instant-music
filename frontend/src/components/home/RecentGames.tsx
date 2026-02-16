import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import type { GameHistory } from '@/types';
import { Link } from 'react-router-dom';

export default function RecentGames() {
  const [games, setGames] = useState<GameHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentGames();
  }, []);

  const fetchRecentGames = async () => {
    try {
      const response = await api.get('/games/history/?limit=5');
      setGames(response.data);
    } catch (err) {
      console.error('Failed to fetch recent games:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'quiz_4':
        return '🎯';
      case 'quiz_fastest':
        return '⚡';
      case 'karaoke':
        return '🎤';
      default:
        return '🎮';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (games.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Aucune partie récente</p>
      </div>
    );
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
                          src={game.winner.avatar}
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
