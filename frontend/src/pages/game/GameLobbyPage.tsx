import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { Game, YouTubePlaylist } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';
import { getMediaUrl } from '../../services/api';

export default function GameLobbyPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [startingGame, setStartingGame] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState<YouTubePlaylist | null>(null);
  const [showPlaylistSelector, setShowPlaylistSelector] = useState(false);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  const { isConnected, sendMessage, onMessage } = useWebSocket(roomCode);
  
  useEffect(() => {
    const unsubscribe = onMessage('message', (data) => {
      console.log('WebSocket message received:', data);
      
      if (data.type === 'player_joined') {
        soundEffects.playerJoined();
        // Update game data with new player info
        if (data.game_data) {
          setGame(data.game_data);
        }
      } else if (data.type === 'player_leave') {
        // Update game data directly from WebSocket message
        if (data.game_data) {
          setGame(data.game_data);
        }
      } else if (data.type === 'broadcast_game_start' || data.type === 'game_started') {
        soundEffects.gameStarted();
        navigate(`/game/play/${roomCode}`);
      }
    });
    return unsubscribe;
  }, [onMessage, navigate, roomCode]);

  useEffect(() => {
    if (roomCode) {
      loadGame();
    }
  }, [roomCode]);

  const loadGame = async () => {
    if (!roomCode) return;

    try {
      setLoading(true);
      const gameData = await gameService.getGame(roomCode);
      setGame(gameData);
      
      // If game already started or finished, redirect
      if (gameData.status === 'in_progress') {
        navigate(`/game/play/${roomCode}`);
        return;
      } else if (gameData.status === 'finished') {
        navigate('/');
        return;
      }
      
      // If not the host and not already in the game, try to join
      if (user && gameData.host !== user.id) {
        const isAlreadyInGame = gameData.players.some((p: any) => p.user === user.id);
        
        if (!isAlreadyInGame) {
          try {
            await gameService.joinGame(roomCode);
            // Reload game data to get updated player list
            const updatedGame = await gameService.getGame(roomCode);
            setGame(updatedGame);
          } catch (joinError: any) {
            // Ignore if already in the game (400 error with specific message)
            const errorMessage = joinError?.response?.data?.error;
            if (!errorMessage?.includes('déjà dans cette partie')) {
              console.error('Failed to join game:', joinError);
              setError('Impossible de rejoindre la partie');
            }
          }
        }
      }
    } catch (err) {
      setError('Impossible de charger la partie');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlaylist = async (playlist: YouTubePlaylist) => {
    if (!game || !roomCode) return;
    
    setSelectedPlaylist(playlist);
    setShowPlaylistSelector(false);
    
    try {
      // Update game with playlist ID via API
      const updatedGame = await gameService.updateGame(roomCode, {
        playlist_id: playlist.youtube_id
      });
      setGame(updatedGame);
    } catch (err) {
      console.error('Failed to update playlist:', err);
      alert('Erreur lors de la mise à jour de la playlist');
    }
  };

  const handleStartGame = async () => {
    if (!game || !user || !roomCode || startingGame) return;

    // Clear previous error
    setStartError(null);
    setStartingGame(true);

    // Check if user is the host
    if (game.host !== user.id) {
      setStartError('Seul l\'hôte peut démarrer la partie');
      setStartingGame(false);
      return;
    }

    // Check if playlist is selected (required for all modes)
    if (!selectedPlaylist && !game.playlist_id) {
      setStartError('Veuillez sélectionner une playlist avant de démarrer');
      setShowPlaylistSelector(true);
      setStartingGame(false);
      return;
    }

    // Check minimum players (karaoke is solo, others need 2+)
    const minPlayers = game.mode === 'karaoke' ? 1 : 2;
    if (game.player_count < minPlayers) {
      setStartError(
        game.mode === 'karaoke'
          ? 'Il faut au moins 1 joueur pour démarrer'
          : 'Il faut au moins 2 joueurs pour démarrer'
      );
      setStartingGame(false);
      return;
    }

    try {
      // Call API to start the game (generates rounds)
      await gameService.startGame(roomCode);
      
      // Notify other players via WebSocket
      sendMessage({
        type: 'start_game',
        room_code: roomCode
      });
      
      // Navigate to game play page
      navigate(`/game/play/${roomCode}`);
    } catch (err: any) {
      console.error('Failed to start game:', err);
      const errorMessage = err?.response?.data?.error || 'Erreur lors du démarrage de la partie';
      
      // Add helpful message for playlist access errors
      if (errorMessage.includes('playlist') && (errorMessage.includes('403') || errorMessage.includes('404'))) {
        setStartError(
          '⚠️ Cette playlist est inaccessible. ' +
          'Veuillez sélectionner une autre playlist publique.'
        );
      } else if (errorMessage.includes('morceaux accessibles') || errorMessage.includes('minimum 4 requis')) {
        setStartError(
          '⚠️ Cette playlist ne contient pas assez de morceaux accessibles. ' +
          'Elle est peut-être privée ou vide. ' +
          'Veuillez en choisir une autre.'
        );
        setShowPlaylistSelector(true);
      } else {
        setStartError(errorMessage);
      }
      setStartingGame(false);
    }
  };

  const handleLeaveGame = () => {
    navigate('/');
  };

  const copyRoomCode = async () => {
    if (roomCode) {
      await navigator.clipboard.writeText(roomCode);
      setCopyMessage('Code copié !');
      setTimeout(() => setCopyMessage(null), 2000);
    }
  };

  const shareGame = async () => {
    const shareUrl = `${window.location.origin}/game/join?code=${roomCode}`;
    const shareData = {
      title: 'Rejoins ma partie InstantMusic !',
      text: `Rejoins ma partie de quiz musical ! Code: ${roomCode}`,
      url: shareUrl,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        // User cancelled or error - fallback to copy
        await navigator.clipboard.writeText(shareUrl);
        setCopyMessage('Lien copié !');
        setTimeout(() => setCopyMessage(null), 2000);
      }
    } else {
      await navigator.clipboard.writeText(shareUrl);
      setCopyMessage('Lien copié !');
      setTimeout(() => setCopyMessage(null), 2000);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Chargement du lobby...</p>
        </div>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto card">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Erreur</h1>
            <p className="text-gray-600 mb-6">{error || 'Partie introuvable'}</p>
            <button onClick={handleLeaveGame} className="btn-primary">
              Retour à l'accueil
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isHost = user?.id === game.host;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {game.name || 'Lobby de jeu'}
              </h1>
              <p className="text-gray-600">
                Mode: <span className="font-semibold">{game.mode}</span>
                {' • '}
                <span className="font-semibold">{game.num_rounds} rounds</span>
                {' • '}
                <span className="font-semibold">{game.round_duration || 30}s/round</span>
                {game.answer_mode === 'text' && (
                  <span className="ml-2 text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">
                    ⌨️ Saisie libre
                  </span>
                )}
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-gray-600">Code de salle:</span>
                <code className="text-2xl font-bold text-primary-600 bg-primary-50 px-3 py-1 rounded-lg tracking-wider">
                  {game.room_code}
                </code>
                <button
                  onClick={copyRoomCode}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title="Copier le code"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                <button
                  onClick={shareGame}
                  className="p-2 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors text-primary-600"
                  title="Partager le lien"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                </button>
              </div>
              {copyMessage && (
                <div className="text-sm text-green-600 font-medium mb-2 animate-pulse">
                  ✓ {copyMessage}
                </div>
              )}
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                {isConnected ? 'Connecté' : 'Déconnecté'}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Players List */}
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="text-xl font-bold mb-4">
                Joueurs ({game.player_count}/{game.max_players})
              </h2>
              <div className="space-y-3">
                {game.players.map((player) => (
                  <div
                    key={player.id}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                  >
                    {player.avatar ? (
                      <img
                        src={getMediaUrl(player.avatar)}
                        alt={player.username}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                        <span className="text-primary-600 font-semibold">
                          {player.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">
                        {player.username}
                        {player.user === game.host && (
                          <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                            Hôte
                          </span>
                        )}
                      </p>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${
                      player.is_connected ? 'bg-green-500' : 'bg-gray-300'
                    }`}></div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Playlist Selection */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Playlist</h2>
                {isHost && (
                  <button
                    onClick={() => setShowPlaylistSelector(!showPlaylistSelector)}
                    className="btn-secondary text-sm"
                  >
                    {showPlaylistSelector ? 'Masquer' : 'Changer'}
                  </button>
                )}
              </div>

              {selectedPlaylist || game.playlist_id ? (
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                  {selectedPlaylist?.image_url && (
                    <img
                      src={selectedPlaylist.image_url}
                      alt={selectedPlaylist.name}
                      className="w-20 h-20 rounded-md object-cover"
                    />
                  )}
                  <div>
                    <h3 className="font-semibold">
                      {selectedPlaylist?.name || 'Playlist sélectionnée'}
                    </h3>
                    {selectedPlaylist && (
                      <p className="text-sm text-gray-600">
                        {selectedPlaylist.total_tracks} morceaux • {selectedPlaylist.owner}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-gray-600 text-center py-4">
                  {isHost ? 'Sélectionnez une playlist pour commencer' : 'En attente de la sélection de l\'hôte...'}
                </p>
              )}

              {showPlaylistSelector && isHost && (
                <div className="mt-4 border-t pt-4">
                  <PlaylistSelector
                    onSelectPlaylist={handleSelectPlaylist}
                    selectedPlaylistId={selectedPlaylist?.youtube_id || game.playlist_id}
                  />
                </div>
              )}
            </div>

            {/* Game Actions */}
            <div className="card">
              <div className="flex items-center justify-between gap-4">
                <button
                  onClick={handleLeaveGame}
                  className="btn-secondary flex-1"
                >
                  Quitter
                </button>
                {isHost && (
                  <button
                    onClick={handleStartGame}
                    className="btn-primary flex-1"
                    disabled={(game.mode === 'karaoke' ? game.player_count < 1 : game.player_count < 2) || startingGame}
                  >
                    {startingGame ? 'Démarrage...' : 'Démarrer la partie'}
                  </button>
                )}
              </div>
              {isHost && game.mode !== 'karaoke' && game.player_count < 2 && (
                <p className="text-sm text-orange-600 text-center mt-2">
                  Il faut au moins 2 joueurs pour démarrer
                </p>
              )}
              {startError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800 text-center">{startError}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

