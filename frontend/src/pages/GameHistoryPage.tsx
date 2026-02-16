import { useState, useEffect } from 'react';
import { api, getMediaUrl } from '@/services/api';
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
                  <button
                    onClick={() => {
                      // Toggle details for this game
                      const gameCard = document.getElementById(`game-details-${game.id}`);
                      if (gameCard) {
                        gameCard.classList.toggle('hidden');
                      }
                    }}
                    className="btn-secondary text-sm"
                  >
                    Détails
                  </button>
                </div>
              </div>

              {/* Expandable Details */}
              <div id={`game-details-${game.id}`} className="hidden mt-6 pt-6 border-t border-gray-200">
                <h4 className="font-bold mb-4">Classement des joueurs</h4>
                <div className="space-y-2">
                  {game.participants.map((participant) => (
                    <div
                      key={participant.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center font-bold text-sm">
                          {participant.rank}
                        </div>
                        <div className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden flex-shrink-0">
                          {participant.avatar ? (
                            <img
                              src={getMediaUrl(participant.avatar)}
                              alt={participant.username}
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
                        <span className="font-medium">{participant.username}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-primary-600">{participant.score} pts</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
