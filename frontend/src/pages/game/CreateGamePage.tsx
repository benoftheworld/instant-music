import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { GameMode, YouTubePlaylist, CreateGameData } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';

const gameModes: { value: GameMode; label: string; description: string }[] = [
  {
    value: 'quiz_4',
    label: 'Quiz 4 Réponses',
    description: 'Choisissez la bonne réponse parmi 4 propositions'
  },
  {
    value: 'quiz_fastest',
    label: 'Quiz Le Plus Rapide',
    description: 'Répondez le plus vite possible pour gagner des points bonus'
  },
  {
    value: 'karaoke',
    label: 'Karaoké',
    description: 'Chantez et devinez les paroles des morceaux'
  }
];

export default function CreateGamePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [gameName, setGameName] = useState('');
  const [gameMode, setGameMode] = useState<GameMode>('quiz_4');
  const [maxPlayers, setMaxPlayers] = useState(8);
  const [numRounds, setNumRounds] = useState(10);
  const [isOnline, setIsOnline] = useState(true);
  const [selectedPlaylist, setSelectedPlaylist] = useState<YouTubePlaylist | null>(null);
  const [showPlaylistSelector, setShowPlaylistSelector] = useState(false);

  const handleCreateGame = async () => {
    // Validate playlist for quiz modes
    if (gameMode !== 'karaoke' && !selectedPlaylist) {
      setError('Veuillez sélectionner une playlist');
      setShowPlaylistSelector(true);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const gameData: CreateGameData = {
        name: gameName || undefined,
        mode: gameMode,
        max_players: maxPlayers,
        num_rounds: numRounds,
        playlist_id: selectedPlaylist?.youtube_id,
        is_online: isOnline
      };

      const game = await gameService.createGame(gameData);
      
      // Navigate to lobby
      navigate(`/game/lobby/${game.room_code}`);
    } catch (err) {
      console.error('Failed to create game:', err);
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Erreur lors de la création de la partie');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Retour
          </button>
          <h1 className="text-4xl font-bold">Créer une partie</h1>
          <p className="text-gray-600 mt-2">
            Configurez votre partie et invitez vos amis à vous rejoindre
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Game Mode Selection */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Mode de jeu</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {gameModes.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setGameMode(mode.value)}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-all
                    ${gameMode === mode.value
                      ? 'border-primary-600 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                    }
                  `}
                >
                  <h3 className="font-semibold mb-2">{mode.label}</h3>
                  <p className="text-sm text-gray-600">{mode.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Game Settings */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Paramètres</h2>
            <div className="space-y-4">
              {/* Game Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom de la partie (optionnel)
                </label>
                <input
                  type="text"
                  maxLength={100}
                  placeholder="Ex: Soirée Quiz 80's"
                  value={gameName}
                  onChange={(e) => setGameName(e.target.value)}
                  className="input max-w-md"
                />
              </div>

              {/* Number of Rounds */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre de rounds
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={numRounds}
                    onChange={(e) => setNumRounds(parseInt(e.target.value))}
                    className="w-48"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[3rem]">
                    {numRounds}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Chaque round dure 30 secondes
                </p>
              </div>

              {/* Max Players */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre maximum de joueurs
                </label>
                <input
                  type="number"
                  min="2"
                  max="20"
                  value={maxPlayers}
                  onChange={(e) => setMaxPlayers(parseInt(e.target.value) || 2)}
                  className="input max-w-xs"
                />
              </div>

              {/* Online/Offline */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="isOnline"
                  checked={isOnline}
                  onChange={(e) => setIsOnline(e.target.checked)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="isOnline" className="text-sm font-medium text-gray-700">
                  Partie en ligne (multijoueur)
                </label>
              </div>
            </div>
          </div>

          {/* Playlist Selection */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Playlist YouTube</h2>
              <button
                onClick={() => setShowPlaylistSelector(!showPlaylistSelector)}
                className="btn-secondary text-sm"
              >
                {selectedPlaylist ? 'Changer' : 'Sélectionner'}
              </button>
            </div>

            {selectedPlaylist ? (
              <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                {selectedPlaylist.image_url && (
                  <img
                    src={selectedPlaylist.image_url}
                    alt={selectedPlaylist.name}
                    className="w-20 h-20 rounded-md object-cover"
                  />
                )}
                <div className="flex-1">
                  <h3 className="font-semibold">{selectedPlaylist.name}</h3>
                  <p className="text-sm text-gray-600">
                    {selectedPlaylist.total_tracks} morceaux • {selectedPlaylist.owner}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedPlaylist(null)}
                  className="text-red-600 hover:text-red-700 p-2"
                  title="Retirer"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                </svg>
                <p className="text-gray-600">Aucune playlist sélectionnée</p>
                {gameMode !== 'karaoke' && (
                  <p className="text-sm text-orange-600 mt-1">
                    Une playlist est requise pour ce mode de jeu
                  </p>
                )}
              </div>
            )}

            {showPlaylistSelector && (
              <div className="mt-4 border-t pt-4">
                <PlaylistSelector
                  onSelectPlaylist={(playlist) => {
                    setSelectedPlaylist(playlist);
                    setShowPlaylistSelector(false);
                    setError(null);
                  }}
                  selectedPlaylistId={selectedPlaylist?.youtube_id}
                />
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="card">
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/')}
                className="btn-secondary flex-1"
                disabled={loading}
              >
                Annuler
              </button>
              <button
                onClick={handleCreateGame}
                className="btn-primary flex-1"
                disabled={loading || (gameMode !== 'karaoke' && !selectedPlaylist)}
              >
                {loading ? 'Création...' : 'Créer la partie'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
