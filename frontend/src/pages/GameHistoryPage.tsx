import { useState, useEffect } from 'react';
import { api, getMediaUrl } from '@/services/api';
import { getModeIcon } from '@/constants/gameModes';
import type { GameHistory } from '@/types';
import { Link } from 'react-router-dom';

export default function GameHistoryPage() {
  const [games, setGames] = useState<GameHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchGameHistory();
  }, []);

  const fetchGameHistory = async () => {
    try {
      setLoading(true);
      const response = await api.get('/games/history/');
      setGames(response.data);
    } catch (err) {
      console.error('Failed to fetch game history:', err);
      setError('Impossible de charger l\'historique des parties');
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Historique des parties</h1>
        <p className="text-gray-600">Toutes les parties terminées</p>
      </div>

      {games.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">Aucune partie terminée pour le moment</p>
          <Link to="/create-game" className="btn-primary">
            Créer une partie
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {games.map((game) => (
            <div key={game.id} className="card hover:shadow-lg transition-shadow">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                {/* Game Info */}
                <div className="md:col-span-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{getModeIcon(game.mode)}</span>
                    <div>
                      <h3 className="font-bold text-lg">{game.mode_display}</h3>
                      <p className="text-sm text-gray-500">Salle: {game.room_code}</p>
                    </div>
                  </div>
                </div>

                {/* Winner */}
                <div className="md:col-span-3">
                  {game.winner ? (
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center flex-shrink-0">
                        {game.winner.avatar ? (
                          <img
                            src={getMediaUrl(game.winner.avatar)}
                            alt={game.winner.username}
                            className="w-full h-full rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-white text-xl">👑</span>
                        )}
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Vainqueur</p>
                        <p className="font-bold">{game.winner.username}</p>
                        <p className="text-sm text-primary-600">{game.winner_score} pts</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500">Aucun vainqueur</p>
                  )}
                </div>

                {/* Stats */}
                <div className="md:col-span-2 text-center">
                  <p className="text-2xl font-bold text-primary-600">{game.player_count}</p>
                  <p className="text-xs text-gray-500 uppercase">Joueurs</p>
                </div>

                {/* Date */}
                <div className="md:col-span-3 text-sm text-gray-600">
                  <p className="mb-1">
                    <span className="font-medium">Hôte:</span> {game.host_username}
                  </p>
                  <p>
                    <span className="font-medium">Terminée:</span> {formatDate(game.finished_at)}
                  </p>
                </div>

                {/* Details Button */}
                <div className="md:col-span-1 text-right">
                  <Link
                    to={`/game/${game.room_code}/results`}
                    className="btn-secondary text-sm inline-block"
                  >
                    Détails
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
