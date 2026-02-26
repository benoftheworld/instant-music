import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import type { Game } from '../../types';

const MODE_LABELS: Record<string, { label: string; icon: string }> = {
  classique: { label: 'Classique', icon: '🎵' },
  rapide: { label: 'Rapide', icon: '⚡' },
  generation: { label: 'Génération', icon: '📅' },
  paroles: { label: 'Paroles', icon: '📝' },
  karaoke: { label: 'Karaoké', icon: '🎤' },
};

export default function JoinGamePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [roomCode, setRoomCode] = useState(searchParams.get('code') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Public games
  const [publicGames, setPublicGames] = useState<Game[]>([]);
  const [publicLoading, setPublicLoading] = useState(true);
  const [publicSearch, setPublicSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'code' | 'public'>('public');

  const loadPublicGames = useCallback(async () => {
    setPublicLoading(true);
    try {
      const games = await gameService.getPublicGames(publicSearch || undefined);
      setPublicGames(games);
    } catch (err) {
      console.error('Failed to load public games:', err);
    } finally {
      setPublicLoading(false);
    }
  }, [publicSearch]);

  useEffect(() => {
    loadPublicGames();
    // Refresh every 15 seconds
    const interval = setInterval(loadPublicGames, 15000);
    return () => clearInterval(interval);
  }, [loadPublicGames]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadPublicGames();
    }, 400);
    return () => clearTimeout(timer);
  }, [publicSearch, loadPublicGames]);

  const handleJoinGame = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!roomCode.trim()) {
      setError('Veuillez entrer un code de salle');
      return;
    }

    await joinByCode(roomCode.trim().toUpperCase());
  };

  const joinByCode = async (code: string) => {
    setLoading(true);
    setError(null);

    try {
      const game = await gameService.getGame(code);

      if (game.status === 'finished') {
        setError('Cette partie est terminée');
        return;
      }

      if (game.status === 'in_progress') {
        setError('Cette partie est déjà en cours');
        return;
      }

      if (game.player_count >= game.max_players) {
        setError('Cette partie est complète');
        return;
      }

      await gameService.joinGame(game.room_code);
      navigate(`/game/lobby/${game.room_code}`);
    } catch (err) {
      console.error('Failed to join game:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const error = err as { response?: { status?: number; data?: { error?: string } } };
        if (error.response?.status === 404) {
          setError('Partie introuvable. Vérifiez le code et réessayez.');
        } else if (error.response?.data?.error) {
          setError(error.response.data.error);
        } else {
          setError('Erreur lors de la tentative de rejoindre la partie');
        }
      } else {
        setError('Erreur lors de la tentative de rejoindre la partie');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Retour
          </button>
          <h1 className="text-4xl font-bold mb-2">Rejoindre une partie</h1>
          <p className="text-gray-600">
            Rejoignez une partie publique ou entrez un code de salle
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('public')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'public'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🌐 Parties publiques
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'code'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🔑 Code de salle
          </button>
        </div>

        {/* Tab: Public Games */}
        {activeTab === 'public' && (
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                value={publicSearch}
                onChange={(e) => setPublicSearch(e.target.value)}
                placeholder="Rechercher par nom, hôte, playlist..."
                className="input pl-10 w-full"
              />
              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Loading */}
            {publicLoading && publicGames.length === 0 && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-3 text-gray-600">Chargement des parties...</p>
              </div>
            )}

            {/* Empty State */}
            {!publicLoading && publicGames.length === 0 && (
              <div className="card text-center py-12">
                <div className="text-5xl mb-4">🎮</div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  Aucune partie publique disponible
                </h3>
                <p className="text-gray-500 mb-6">
                  {publicSearch
                    ? 'Aucun résultat pour cette recherche. Essayez un autre terme.'
                    : 'Soyez le premier à créer une partie publique !'}
                </p>
                <button
                  onClick={() => navigate('/game/create')}
                  className="btn-primary"
                >
                  Créer une partie
                </button>
              </div>
            )}

            {/* Games List */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {publicGames.map((game) => {
                const mode = MODE_LABELS[game.mode] || { label: game.mode, icon: '🎵' };
                const isFull = game.player_count >= game.max_players;
                return (
                  <button
                    key={game.id}
                    onClick={() => !isFull && joinByCode(game.room_code)}
                    disabled={isFull || loading}
                    className={`card p-4 text-left transition-all ${
                      isFull
                        ? 'opacity-60 cursor-not-allowed'
                        : 'hover:shadow-lg hover:scale-[1.02] cursor-pointer'
                    }`}
                  >
                    <div className="flex gap-4">
                      {/* Playlist Image */}
                      <div className="w-20 h-20 rounded-lg bg-gray-200 flex-shrink-0 overflow-hidden">
                        {game.playlist_image_url ? (
                          <img
                            src={game.playlist_image_url}
                            alt={game.playlist_name || 'Playlist'}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <span className="text-3xl">{mode.icon}</span>
                          </div>
                        )}
                      </div>

                      {/* Game Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-semibold text-gray-900 truncate">
                            {game.name || `Partie de ${game.host_username}`}
                          </h3>
                          {isFull && (
                            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full flex-shrink-0">
                              Complète
                            </span>
                          )}
                        </div>

                        {/* Playlist name */}
                        {game.playlist_name && (
                          <p className="text-sm text-primary-600 font-medium truncate mt-0.5">
                            🎵 {game.playlist_name}
                          </p>
                        )}

                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                            {mode.icon} {mode.label}
                          </span>
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                            {game.num_rounds} rounds
                          </span>
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                            👥 {game.player_count}/{game.max_players}
                          </span>
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                            ⏱️ {game.round_duration}s
                          </span>
                        </div>

                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            Hôte : {game.host_username}
                          </span>
                          <code className="text-xs font-mono text-gray-400">
                            {game.room_code}
                          </code>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Refresh hint */}
            {publicGames.length > 0 && (
              <p className="text-xs text-gray-400 text-center">
                Mise à jour automatique toutes les 15 secondes
              </p>
            )}
          </div>
        )}

        {/* Tab: Join by Code */}
        {activeTab === 'code' && (
          <div className="max-w-md mx-auto">
            <div className="card">
              <form onSubmit={handleJoinGame} className="space-y-6">
                <div>
                  <label htmlFor="roomCode" className="block text-sm font-medium text-gray-700 mb-2">
                    Code de salle
                  </label>
                  <input
                    type="text"
                    id="roomCode"
                    value={roomCode}
                    onChange={(e) => {
                      setRoomCode(e.target.value.toUpperCase());
                      setError(null);
                    }}
                    placeholder="ABC123"
                    className="input text-center text-2xl font-bold tracking-wider"
                    maxLength={6}
                    disabled={loading}
                    autoFocus
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Le code de 6 caractères fourni par l'hôte de la partie
                  </p>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || !roomCode.trim()}
                  className="btn-primary w-full text-lg"
                >
                  {loading ? 'Connexion...' : 'Rejoindre la partie'}
                </button>
              </form>
            </div>

            {/* Help Section */}
            <div className="mt-8 card bg-blue-50">
              <h3 className="font-semibold text-blue-900 mb-2">💡 Besoin d'aide ?</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Demandez le code de salle à l'hôte de la partie</li>
                <li>• Le code est composé de 6 caractères</li>
                <li>• Assurez-vous que la partie n'a pas encore commencé</li>
              </ul>
            </div>
          </div>
        )}

        {/* Create Game Link */}
        <div className="mt-8 text-center">
          <p className="text-gray-600 mb-3">Vous n'avez pas de code ?</p>
          <button
            onClick={() => navigate('/game/create')}
            className="btn-secondary"
          >
            Créer votre propre partie
          </button>
        </div>
      </div>
    </div>
  );
}
