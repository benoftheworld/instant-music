import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { gameService } from '../../services/gameService';
import { Game, SpotifyPlaylist } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';

export default function GameLobbyPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [selectedPlaylist, setSelectedPlaylist] = useState<SpotifyPlaylist | null>(null);
  const [showPlaylistSelector, setShowPlaylistSelector] = useState(false);

  const { isConnected, sendMessage, onMessage } = useWebSocket(roomCode);
  
  useEffect(() => {
    const unsubscribe = onMessage('message', (data) => {
      console.log('WebSocket message received:', data);
      
      if (data.type === 'player_joined') {
        // Update game data with new player info
        if (data.game_data) {
          setGame(data.game_data);
        } else {
          // Fallback: reload game
          loadGame();
        }
      } else if (data.type === 'player_leave') {
        loadGame();
      } else if (data.type === 'broadcast_game_start' || data.type === 'game_started') {
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
      
      // If not the host, try to join the game (ignore if already joined)
      if (user && gameData.host !== user.id) {
        try {
          await gameService.joinGame(roomCode);
          // No need to reload or send WS - backend handles it
        } catch (joinError: any) {
          // Ignore if already in the game (400 error)
          if (joinError?.response?.status !== 400) {
            console.error('Failed to join game:', joinError);
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

  const handleSelectPlaylist = async (playlist: SpotifyPlaylist) => {
    if (!game || !roomCode) return;
    
    setSelectedPlaylist(playlist);
    setShowPlaylistSelector(false);
    
    try {
      // Update game with playlist ID via API
      const updatedGame = await gameService.updateGame(roomCode, {
        playlist_id: playlist.spotify_id
      });
      setGame(updatedGame);
    } catch (err) {
      console.error('Failed to update playlist:', err);
      alert('Erreur lors de la mise à jour de la playlist');
    }
  };

  const handleStartGame = async () => {
    if (!game || !user || !roomCode) return;

    // Clear previous error
    setStartError(null);

    // Check if user is the host
    if (game.host !== user.id) {
      setStartError('Seul l\'hôte peut démarrer la partie');
      return;
    }

    // Check if playlist is selected (for quiz modes)
    if (game.mode !== 'karaoke' && !selectedPlaylist && !game.playlist_id) {
      setStartError('Veuillez sélectionner une playlist avant de démarrer');
      setShowPlaylistSelector(true);
      return;
    }

    // Check minimum players
    if (game.player_count < 2) {
      setStartError('Il faut au moins 2 joueurs pour démarrer');
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
      if (errorMessage.includes('playlist') && errorMessage.includes('403')) {
        setStartError(
          '⚠️ Cette playlist est privée ou inaccessible. ' +
          'Veuillez sélectionner une playlist PUBLIQUE différente.'
        );
      } else if (errorMessage.includes('morceaux accessibles') || errorMessage.includes('minimum 4 requis')) {
        setStartError(
          '⚠️ Cette playlist ne contient pas assez de morceaux accessibles. ' +
          'Elle est peut-être privée, géo-restreinte, ou vide. ' +
          'Veuillez en choisir une autre (playlist publique recommandée).'
        );
        setShowPlaylistSelector(true);
      } else {
        setStartError(errorMessage);
      }
    }
  };

  const handleLeaveGame = () => {
    navigate('/');
  };

  const copyRoomCode = () => {
    if (roomCode) {
      navigator.clipboard.writeText(roomCode);
      alert('Code de salle copié !');
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
              <h1 className="text-3xl font-bold mb-2">Lobby de jeu</h1>
              <p className="text-gray-600">
                Mode: <span className="font-semibold">{game.mode}</span>
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-gray-600">Code de salle:</span>
                <code className="text-2xl font-bold text-primary-600">{game.room_code}</code>
                <button
                  onClick={copyRoomCode}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title="Copier le code"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
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
                        src={player.avatar}
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
                    selectedPlaylistId={selectedPlaylist?.spotify_id || game.playlist_id}
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
                    disabled={game.player_count < 2}
                  >
                    Démarrer la partie
                  </button>
                )}
              </div>
              {isHost && game.player_count < 2 && (
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

