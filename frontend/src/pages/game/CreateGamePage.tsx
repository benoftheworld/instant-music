import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import type { GameMode, AnswerMode, GuessTarget, YouTubePlaylist, KaraokeSong, CreateGameData } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';
import KaraokeSongSelector from '../../components/karaoke/KaraokeSongSelector';

const TOTAL_STEPS = 4;

const gameModes: { value: GameMode; label: string; description: string; icon: string }[] = [
  {
    value: 'classique',
    label: 'Classique',
    description: 'La musique se lance au début du round. Trouvez l\'artiste ou le titre.',
    icon: '🎵',
  },
  {
    value: 'rapide',
    label: 'Rapide',
    description: '3 secondes de musique puis silence. Trouvez l\'artiste ou le titre.',
    icon: '⚡',
  },
  {
    value: 'generation',
    label: 'Génération',
    description: 'Devinez l\'année de sortie du morceau. Points selon la précision.',
    icon: '📅',
  },
  {
    value: 'paroles',
    label: 'Paroles',
    description: 'Complétez les paroles manquantes. Aucune musique pendant le round.',
    icon: '📝',
  },
  {
    value: 'karaoke',
    label: 'Karaoké',
    description: 'Mode solo : la musique complète joue via YouTube et les paroles défilent en rythme.',
    icon: '🎤',
  },
];

export default function CreateGamePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  // Step 1: Game mode
  const [selectedMode, setSelectedMode] = useState<GameMode>('classique');
  const [answerMode, setAnswerMode] = useState<AnswerMode>('mcq');
  const [guessTarget, setGuessTarget] = useState<GuessTarget>('title');
  const [lyricsWordsCount, setLyricsWordsCount] = useState(3);

  // Step 2: Global config (non-karaoke only)
  const [roundDuration, setRoundDuration] = useState(30);
  const [scoreDisplayDuration, setScoreDisplayDuration] = useState(10);
  const [maxPlayers, setMaxPlayers] = useState(8);
  const [numRounds, setNumRounds] = useState(10);
  const [isOnline, setIsOnline] = useState(true);

  // Step 3: Playlist (non-karaoke) or karaoke song
  const [selectedPlaylist, setSelectedPlaylist] = useState<YouTubePlaylist | null>(null);
  const [karaokeSelectedSong, setKaraokeSelectedSong] = useState<KaraokeSong | null>(null);

  const isKaraoke = selectedMode === 'karaoke';

  const TOTAL_STEPS = isKaraoke ? 3 : 4;

  // Step navigation — karaoke skips step 2 (global config)
  const nextStep = () => {
    if (currentStep === 1 && isKaraoke) {
      setCurrentStep(3); // jump straight to track selection
    } else if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep === 3 && isKaraoke) {
      setCurrentStep(1); // jump back to mode selection
    } else if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return true;
      case 2: return true;
      case 3: return isKaraoke ? !!karaokeSelectedSong : !!selectedPlaylist;
      default: return true;
    }
  };

  const handleCreateGame = async () => {
    if (isKaraoke) {
      if (!karaokeSelectedSong) {
        setError('Veuillez sélectionner un morceau dans le catalogue');
        setCurrentStep(3);
        return;
      }
    } else {
      if (!selectedPlaylist) {
        setError('Veuillez sélectionner une playlist');
        setCurrentStep(3);
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const gameData: CreateGameData = {
        mode: selectedMode,
        max_players: isKaraoke ? 1 : maxPlayers,
        num_rounds: isKaraoke ? 1 : numRounds,
        playlist_id: isKaraoke ? undefined : selectedPlaylist?.youtube_id,
        karaoke_song_id: isKaraoke ? karaokeSelectedSong!.id : undefined,
        is_online: isKaraoke ? false : isOnline,
        answer_mode: answerMode,
        guess_target: guessTarget,
        round_duration: roundDuration,
        score_display_duration: isKaraoke ? 0 : scoreDisplayDuration,
        lyrics_words_count: selectedMode === 'paroles' ? lyricsWordsCount : undefined,
      };

      const game = await gameService.createGame(gameData);
      navigate(`/game/lobby/${game.room_code}`);
    } catch (err) {
      console.error('Failed to create game:', err);
      const error = err as { response?: { data?: { error?: string; non_field_errors?: string[] } } };
      const msg = error.response?.data?.error
        || error.response?.data?.non_field_errors?.[0]
        || 'Erreur lors de la création de la partie';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const renderStepIndicator = () => {
    // Karaoke: only steps 1, 3, 4 (step 2 is skipped)
    const visibleSteps = isKaraoke ? [1, 3, 4] : [1, 2, 3, 4];
    const activeIndex = visibleSteps.indexOf(currentStep);

    return (
      <div className="flex items-center justify-center mb-8">
        {visibleSteps.map((step, idx) => (
          <div key={step} className="flex items-center">
            <button
              onClick={() => activeIndex > idx && setCurrentStep(step)}
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                step === currentStep
                  ? 'bg-primary-600 text-white shadow-lg scale-110'
                  : activeIndex > idx
                  ? 'bg-primary-200 text-primary-700 cursor-pointer hover:bg-primary-300'
                  : 'bg-gray-200 text-gray-400'
              }`}
            >
              {activeIndex > idx ? '✓' : idx + 1}
            </button>
            {idx < visibleSteps.length - 1 && (
              <div
                className={`w-16 h-1 mx-1 rounded ${
                  activeIndex > idx ? 'bg-primary-400' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderStepTitle = () => {
    const titles: Record<number, string> = {
      1: 'Mode de jeu',
      2: 'Configuration globale',
      3: isKaraoke ? 'Sélection du morceau' : 'Sélection de la playlist',
      4: 'Confirmation',
    };
    const subtitles: Record<number, string> = {
      1: 'Choisissez votre mode de jeu et ses options',
      2: 'Paramétrez les timers, le nombre de joueurs et les options générales',
      3: isKaraoke
        ? 'Choisissez un morceau dans le catalogue karaoké'
        : 'Choisissez la playlist musicale pour la partie',
      4: 'Vérifiez vos choix et lancez la partie',
    };
    return (
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold">{titles[currentStep]}</h2>
        <p className="text-gray-600 text-sm mt-1">{subtitles[currentStep]}</p>
      </div>
    );
  };

  const renderStep1 = () => (
    <div className="card space-y-6">
      {/* Round duration — hidden for karaoke (auto from video length) */}
      {!isKaraoke && (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          🎵 Temps du round
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
          Durée pour répondre à chaque question
        </p>
      </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          🏆 Temps affichage score fin de round
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="3"
            max="30"
            value={scoreDisplayDuration}
            onChange={(e) => setScoreDisplayDuration(parseInt(e.target.value))}
            className="w-48"
          />
          <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
            {scoreDisplayDuration}s
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Durée d'affichage des résultats après chaque round
        </p>
      </div>

      {/* Max players & rounds — hidden for karaoke (solo, 1 round) */}
      {!isKaraoke && (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            👥 Nombre maximum de joueurs
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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🔄 Nombre de rounds
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
      </div>
      )}

      <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
        <input
          type="checkbox"
          id="isOffline"
          checked={!isOnline}
          onChange={(e) => setIsOnline(!e.target.checked)}
          className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label htmlFor="isOffline" className="text-sm font-medium text-gray-700">
          📴 Mode hors ligne (solo)
        </label>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      {/* Mode selection */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Choisissez un mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gameModes.map((mode) => {
            const isSelected = selectedMode === mode.value;
            return (
              <button
                key={mode.value}
                onClick={() => {
                  setSelectedMode(mode.value);
                  if (mode.value === 'karaoke') setMaxPlayers(1);
                }}
                className={`p-5 rounded-xl border-2 text-left transition-all relative ${
                  isSelected
                    ? 'border-primary-600 bg-primary-50 shadow-md'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                {isSelected && (
                  <span className="absolute top-3 right-3 text-primary-600">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
                <div className="text-3xl mb-2">{mode.icon}</div>
                <h4 className="font-bold text-lg mb-1">{mode.label}</h4>
                <p className="text-sm text-gray-600">{mode.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Mode-specific config */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Configuration du mode</h3>

        {/* Answer mode — hidden for karaoke (solo, no guessing) */}
        {selectedMode !== 'karaoke' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
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
                <p className="text-xs text-gray-500 mt-1">Écrire la réponse</p>
              </button>
            </div>
          </div>
        )}

        {/* Classique / Rapide specific */}
        {(selectedMode === 'classique' || selectedMode === 'rapide') && (
          <div className="space-y-4">
            {answerMode === 'mcq' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Que doit trouver le joueur ?
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setGuessTarget('title')}
                    className={`flex-1 p-3 rounded-lg border-2 text-center transition-all ${
                      guessTarget === 'title'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-xl mb-1">🎵</div>
                    <div className="font-semibold text-sm">Le titre</div>
                  </button>
                  <button
                    onClick={() => setGuessTarget('artist')}
                    className={`flex-1 p-3 rounded-lg border-2 text-center transition-all ${
                      guessTarget === 'artist'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-xl mb-1">🎤</div>
                    <div className="font-semibold text-sm">L'artiste</div>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">
                  <strong>💡 Saisie libre :</strong> Le joueur peut tenter de trouver l'artiste <strong>et/ou</strong> le titre.
                  S'il trouve les deux, il <strong>double ses points</strong> !
                </p>
              </div>
            )}

            {selectedMode === 'rapide' && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>⚡ Mode Rapide :</strong> La musique se joue pendant <strong>3 secondes</strong> puis s'arrête.
                  Le joueur a ensuite tout le temps restant du round pour répondre.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Paroles specific */}
        {selectedMode === 'paroles' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de mots à trouver
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={lyricsWordsCount}
                  onChange={(e) => setLyricsWordsCount(parseInt(e.target.value))}
                  className="w-48"
                />
                <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                  {lyricsWordsCount} mot{lyricsWordsCount > 1 ? 's' : ''}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Nombre de mots masqués dans les paroles
              </p>
            </div>

            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="text-sm text-purple-800">
                <strong>📝 Mode Paroles :</strong> Aucune musique ne joue pendant le round.
                Les joueurs doivent compléter les paroles affichées.
                {answerMode === 'mcq'
                  ? ' Des propositions seront affichées.'
                  : ' Les joueurs saisissent les mots manquants.'}
              </p>
            </div>
          </div>
        )}

        {/* Génération specific */}
        {selectedMode === 'generation' && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              <strong>📅 Mode Génération :</strong> Devinez l'année de sortie de la musique.
            </p>
            <ul className="text-sm text-green-700 mt-2 space-y-1 ml-4">
              <li>🎯 <strong>Année exacte :</strong> Points maximum</li>
              <li>📌 <strong>± 2 ans :</strong> Points conséquents</li>
              <li>📎 <strong>± 5 ans :</strong> Quelques points</li>
              <li>❌ <strong>Au-delà :</strong> Aucun point</li>
            </ul>
          </div>
        )}

        {/* Karaoké specific */}
        {selectedMode === 'karaoke' && (
          <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
            <p className="text-sm text-pink-800">
              <strong>🎤 Mode Karaoké (solo) :</strong> La musique complète joue via YouTube
              et les paroles défilent en rythme. Chantez et profitez !
            </p>
            <ul className="text-sm text-pink-700 mt-2 space-y-1 ml-4">
              <li>▶️ <strong>YouTube :</strong> La chanson complète joue (pas un extrait de 30s)</li>
              <li>📜 <strong>Paroles synchronisées :</strong> Les paroles s'affichent en rythme (LRCLib)</li>
              <li>🎤 <strong>Bientôt :</strong> Reconnaissance vocale pour gagner des points</li>
              <li>👤 <strong>Solo :</strong> Ce mode se joue seul, pas besoin d'adversaire</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="card">
      {isKaraoke ? (
        <KaraokeSongSelector
          selectedSong={karaokeSelectedSong}
          onSelectSong={(song) => {
            setKaraokeSelectedSong(song);
            setError(null);
          }}
        />
      ) : (
        <>
          {selectedPlaylist ? (
            <div className="mb-6">
              <div className="flex items-center gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                {selectedPlaylist.image_url && (
                  <img
                    src={selectedPlaylist.image_url}
                    alt={selectedPlaylist.name}
                    className="w-20 h-20 rounded-md object-cover"
                  />
                )}
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{selectedPlaylist.name}</h3>
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
            </div>
          ) : (
            <div className="text-center py-4 mb-4">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
              </svg>
              <p className="text-gray-600">Sélectionnez une playlist ci-dessous</p>
            </div>
          )}

          <PlaylistSelector
            onSelectPlaylist={(playlist) => {
              setSelectedPlaylist(playlist);
              setError(null);
            }}
            selectedPlaylistId={selectedPlaylist?.youtube_id}
          />
        </>
      )}
    </div>
  );

  const renderStep4 = () => {
    const modeConfig = gameModes.find((m) => m.value === selectedMode);

    return (
      <div className="card space-y-6">
        <h3 className="text-lg font-bold">Récapitulatif</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Global config summary */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Configuration</h4>
            <ul className="space-y-2 text-sm">
              <li><span className="text-gray-500">⏳ Timer début :</span> <strong>5s</strong></li>
              {!isKaraoke && (
                <>
                  <li><span className="text-gray-500">Durée round :</span> <strong>{roundDuration}s</strong></li>
                  <li><span className="text-gray-500">Rounds :</span> <strong>{numRounds}</strong></li>
                  <li><span className="text-gray-500">Joueurs max :</span> <strong>{maxPlayers}</strong></li>
                  <li><span className="text-gray-500">Score affichage :</span> <strong>{scoreDisplayDuration}s</strong></li>
                  <li><span className="text-gray-500">Mode :</span> <strong>{isOnline ? 'En ligne' : 'Hors ligne'}</strong></li>
                </>
              )}
              {isKaraoke && (
                <>
                  <li><span className="text-gray-500">Round :</span> <strong>1 (durée auto)</strong></li>
                  <li><span className="text-gray-500">Mode :</span> <strong>Hors ligne / solo</strong></li>
                </>
              )}
            </ul>
          </div>

          {/* Mode summary */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Mode de jeu</h4>
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{modeConfig?.icon}</span>
              <div>
                <p className="font-bold">{modeConfig?.label}</p>
                <p className="text-xs text-gray-600">{modeConfig?.description}</p>
              </div>
            </div>
            {!isKaraoke && (
              <ul className="space-y-2 text-sm">
                <li>
                  <span className="text-gray-500">Réponse :</span>{' '}
                  <strong>{answerMode === 'mcq' ? 'QCM' : 'Saisie libre'}</strong>
                </li>
                {(selectedMode === 'classique' || selectedMode === 'rapide') && answerMode === 'mcq' && (
                  <li>
                    <span className="text-gray-500">Cible :</span>{' '}
                    <strong>{guessTarget === 'artist' ? 'Artiste' : 'Titre'}</strong>
                  </li>
                )}
                {selectedMode === 'paroles' && (
                  <li>
                    <span className="text-gray-500">Mots à trouver :</span>{' '}
                    <strong>{lyricsWordsCount}</strong>
                  </li>
                )}
              </ul>
            )}
          </div>
        </div>

        {/* Karaoke song summary */}
        {isKaraoke && karaokeSelectedSong && (
          <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
            <h4 className="font-semibold text-sm text-pink-600 uppercase mb-3">🎤 Morceau karaoké</h4>
            <div className="flex items-center gap-4">
              {karaokeSelectedSong.album_image_url && (
                <img
                  src={karaokeSelectedSong.album_image_url}
                  alt={karaokeSelectedSong.title}
                  className="w-16 h-16 rounded-md object-cover"
                />
              )}
              <div>
                <p className="font-bold">{karaokeSelectedSong.title}</p>
                <p className="text-sm text-gray-600">{karaokeSelectedSong.artist}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-400">{karaokeSelectedSong.duration_display}</span>
                  {karaokeSelectedSong.lrclib_id ? (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">
                      ✓ Paroles synchronisées
                    </span>
                  ) : (
                    <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                      ⚠ Recherche auto paroles
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Playlist summary (non-karaoke) */}
        {!isKaraoke && selectedPlaylist && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Playlist</h4>
            <div className="flex items-center gap-4">
              {selectedPlaylist.image_url && (
                <img
                  src={selectedPlaylist.image_url}
                  alt={selectedPlaylist.name}
                  className="w-16 h-16 rounded-md object-cover"
                />
              )}
              <div>
                <p className="font-bold">{selectedPlaylist.name}</p>
                <p className="text-sm text-gray-600">
                  {selectedPlaylist.total_tracks} morceaux • {selectedPlaylist.owner}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
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
        </div>

        {/* Step indicator */}
        {renderStepIndicator()}
        {renderStepTitle()}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Step content */}
        {currentStep === 1 && renderStep2()}
        {currentStep === 2 && renderStep1()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}

        {/* Navigation buttons */}
        <div className="card mt-6">
          <div className="flex gap-4">
            {currentStep === 1 ? (
              <button
                onClick={() => navigate('/')}
                className="btn-secondary flex-1"
              >
                Annuler
              </button>
            ) : (
              <button
                onClick={prevStep}
                className="btn-secondary flex-1"
              >
                ← Précédent
              </button>
            )}

            {currentStep < TOTAL_STEPS ? (
              <button
                onClick={nextStep}
                className="btn-primary flex-1"
                disabled={!canProceed()}
              >
                Suivant →
              </button>
            ) : (
              <button
                onClick={handleCreateGame}
                className="btn-primary flex-1"
                disabled={loading || (isKaraoke ? !karaokeSelectedSong : !selectedPlaylist)}
              >
                {loading ? 'Création...' : 'Créer la partie'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
