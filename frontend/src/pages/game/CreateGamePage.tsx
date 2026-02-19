import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { GameMode, AnswerMode, YouTubePlaylist, CreateGameData } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';

const gameModes: { value: GameMode; label: string; description: string; icon: string; disabled?: boolean }[] = [
  {
    value: 'quiz_4',
    label: 'Classique',
    description: 'Trouvez le bon titre parmi 4 propositions',
    icon: '🎵',
  },
  {
    value: 'blind_test_inverse',
    label: 'Trouver le Titre',
    description: "L'artiste est donné, trouvez le titre (plus facile)",
    icon: '🎯',
  },
  {
    value: 'guess_year',
    label: 'Année de Sortie',
    description: 'Devinez l\'année de sortie du morceau (±2 ans)',
    icon: '📅',
  },
  {
    value: 'guess_artist',
    label: 'Trouver l\'Artiste',
    description: 'Le titre est donné, trouvez qui interprète le morceau',
    icon: '🎤',
  },
  {
    value: 'intro',
    label: 'Intro (3s)',
    description: 'Reconnaissez le morceau en seulement 3 secondes',
    icon: '⚡',
  },
  {
    value: 'lyrics',
    label: 'Lyrics',
    description: 'Complétez les paroles manquantes du morceau',
    icon: '📝',
  },
];

export default function CreateGamePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [gameName, setGameName] = useState('');
  const [selectedModes, setSelectedModes] = useState<GameMode[]>(['quiz_4']);
  const [maxPlayers, setMaxPlayers] = useState(8);
  const [numRounds, setNumRounds] = useState(10);
  const [isOnline, setIsOnline] = useState(true);
  const [answerMode, setAnswerMode] = useState<AnswerMode>('mcq');
  const [roundDuration, setRoundDuration] = useState(30);
  const [timeBetweenRounds, setTimeBetweenRounds] = useState(10);
  const [lyricsWordsCount, setLyricsWordsCount] = useState(1);
  const [selectedPlaylist, setSelectedPlaylist] = useState<YouTubePlaylist | null>(null);
  const [showPlaylistSelector, setShowPlaylistSelector] = useState(false);

  const toggleMode = (mode: GameMode) => {
    setSelectedModes(prev => {
      if (prev.includes(mode)) {
        // Don't allow removing the last mode
        if (prev.length === 1) return prev;
        return prev.filter(m => m !== mode);
      }
      return [...prev, mode];
    });
  };

  const handleCreateGame = async () => {
    // Validate playlist selection
    if (!selectedPlaylist) {
      setError('Veuillez sélectionner une playlist');
      setShowPlaylistSelector(true);
      return;
    }

    if (selectedModes.length === 0) {
      setError('Veuillez sélectionner au moins un mode de jeu');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const gameData: CreateGameData = {
        name: gameName || undefined,
        mode: selectedModes[0], // Primary mode for backwards compatibility
        modes: selectedModes,   // All selected modes
        max_players: maxPlayers,
        num_rounds: numRounds,
        playlist_id: selectedPlaylist?.youtube_id,
        is_online: isOnline,
        answer_mode: answerMode,
        round_duration: roundDuration,
        lyrics_words_count: lyricsWordsCount,
        time_between_rounds: timeBetweenRounds,
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
            <h2 className="text-xl font-bold mb-4">Modes de jeu</h2>
            <p className="text-sm text-gray-600 mb-4">
              Sélectionnez un ou plusieurs modes. Les questions seront mélangées entre les modes choisis.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {gameModes.map((mode) => {
                const isSelected = selectedModes.includes(mode.value);
                return (
                  <button
                    key={mode.value}
                    onClick={() => !mode.disabled && toggleMode(mode.value)}
                    disabled={mode.disabled}
                    className={`
                      p-4 rounded-lg border-2 text-left transition-all relative
                      ${mode.disabled
                        ? 'border-gray-200 bg-gray-100 opacity-50 cursor-not-allowed'
                        : isSelected
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }
                    `}
                  >
                    {isSelected && (
                      <span className="absolute top-2 right-2 text-primary-600">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </span>
                    )}
                    <div className="text-2xl mb-2">{mode.icon}</div>
                    <h3 className="font-semibold mb-1">{mode.label}</h3>
                    <p className="text-xs text-gray-600">{mode.description}</p>
                    {mode.disabled && (
                      <span className="absolute top-2 right-2 text-xs bg-gray-300 text-gray-600 px-2 py-0.5 rounded-full font-medium">
                        Bientôt
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            {selectedModes.length > 1 && (
              <p className="text-sm text-primary-600 mt-3 font-medium">
                ✨ Mode mixte : {selectedModes.length} modes sélectionnés
              </p>
            )}
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

              {/* Answer Mode */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mode de réponse
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setAnswerMode('mcq')}
                    className={`flex-1 p-4 rounded-lg border-2 text-center transition-all ${
                      answerMode === 'mcq'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-2xl mb-1">🔘</div>
                    <div className="font-semibold text-sm">QCM</div>
                    <p className="text-xs text-gray-500 mt-1">4 réponses proposées</p>
                  </button>
                  <button
                    onClick={() => setAnswerMode('text')}
                    className={`flex-1 p-4 rounded-lg border-2 text-center transition-all ${
                      answerMode === 'text'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-2xl mb-1">⌨️</div>
                    <div className="font-semibold text-sm">Saisie libre</div>
                    <p className="text-xs text-gray-500 mt-1">Écrire la réponse (plus difficile)</p>
                  </button>
                </div>
                {answerMode === 'text' && (
                  <p className="text-sm text-amber-600 mt-2">
                    ⚠️ En mode saisie libre, les réponses sont comparées avec tolérance (accents, articles, fautes mineures).
                  </p>
                )}
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
              </div>

              {/* Round Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Durée d'un round
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="10"
                    max="60"
                    step="5"
                    value={roundDuration}
                    onChange={(e) => setRoundDuration(parseInt(e.target.value))}
                    className="w-48"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                    {roundDuration}s
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Temps pour répondre à chaque question
                </p>
              </div>

              {/* Time Between Rounds */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temps entre les rounds
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="3"
                    max="30"
                    value={timeBetweenRounds}
                    onChange={(e) => setTimeBetweenRounds(parseInt(e.target.value))}
                    className="w-48"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                    {timeBetweenRounds}s
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Pause entre chaque round (écran de chargement / résultats)
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

              {/* Lyrics words count (only when Lyrics mode selected) */}
              {selectedModes.includes('lyrics') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre de mots à deviner (Lyrics)
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="1"
                      max="3"
                      value={lyricsWordsCount}
                      onChange={(e) => setLyricsWordsCount(parseInt(e.target.value))}
                      className="w-48"
                    />
                    <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                      {lyricsWordsCount} mot{lyricsWordsCount > 1 ? 's' : ''}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Choisissez combien de mots seront masqués dans chaque question Lyrics.
                  </p>
                </div>
              )}

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
              <h2 className="text-xl font-bold">Playlist</h2>
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
                {selectedModes.length > 0 && !selectedPlaylist && (
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
                disabled={loading || !selectedPlaylist}
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
