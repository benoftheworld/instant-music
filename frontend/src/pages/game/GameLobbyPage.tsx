import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { Game, YouTubePlaylist } from '../../types';
import PlaylistSelector from '../../components/playlist/PlaylistSelector';
import InviteFriendsModal from '../../components/game/InviteFriendsModal';
import { getApiErrorMessage } from '../../utils/apiError';
import LobbyHeader from './lobby/LobbyHeader';
import LobbyPlayerList from './lobby/LobbyPlayerList';
import LobbyActions from './lobby/LobbyActions';

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
  const [showInviteModal, setShowInviteModal] = useState(false);

  const { isConnected, onMessage } = useWebSocket(roomCode);

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
          // If host left and game is cancelled, redirect everyone
          if (data.game_data.status === 'cancelled') {
            navigate('/');
          }
        }
      } else if (data.type === 'game_updated') {
        // Sync any lobby state change (e.g. playlist update by host)
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

  const loadGame = useCallback(async () => {
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
  }, [roomCode, user, navigate]);

  useEffect(() => {
    if (roomCode) {
      loadGame();
    }
  }, [roomCode, loadGame]);

  // On reconnexion WebSocket (après coupure réseau), resynchroniser l'état
  // du jeu depuis l'API pour rattraper les messages manqués pendant la coupure
  useEffect(() => {
    const unsubscribe = onMessage('reconnected', () => {
      console.log('WebSocket reconnected — refreshing game state');
      loadGame();
    });
    return unsubscribe;
  }, [onMessage, loadGame]);

  const handleSelectPlaylist = async (playlist: YouTubePlaylist) => {
    if (!game || !roomCode) return;

    setSelectedPlaylist(playlist);
    setShowPlaylistSelector(false);

    try {
      // Update game with playlist ID and info via API
      const updatedGame = await gameService.updateGame(roomCode, {
        playlist_id: playlist.youtube_id,
        playlist_name: playlist.name,
        playlist_image_url: playlist.image_url,
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

    // Check if playlist is selected (required for non-karaoke modes)
    if (game.mode !== 'karaoke' && !selectedPlaylist && !game.playlist_id) {
      setStartError('Veuillez sélectionner une playlist avant de démarrer');
      setShowPlaylistSelector(true);
      setStartingGame(false);
      return;
    }

    // Check minimum players (solo modes need 1, others need 2+)
    const minPlayers = isSolo ? 1 : 2;
    if (game.player_count < minPlayers) {
      setStartError(
        isSolo
          ? 'Il faut au moins 1 joueur pour démarrer'
          : 'Il faut au moins 2 joueurs pour démarrer'
      );
      setStartingGame(false);
      return;
    }

    try {
      // Call API to start the game (generates rounds).
      // The backend broadcasts game_started to all connected clients,
      // so non-host players navigate via the WebSocket handler above.
      await gameService.startGame(roomCode);

      // Host navigates directly (no need to wait for WS echo).
      navigate(`/game/play/${roomCode}`);
    } catch (err: unknown) {
      console.error('Failed to start game:', err);
      const errorMessage = getApiErrorMessage(err, 'Erreur lors du démarrage de la partie');

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

  const handleLeaveGame = async () => {
    if (roomCode) {
      try {
        await gameService.leaveGame(roomCode);
      } catch (err) {
        console.error('Failed to leave game:', err);
      }
    }
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
  const isSolo = game.mode === 'karaoke' || !game.is_online;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <LobbyHeader
          game={game}
          isConnected={isConnected}
          copyMessage={copyMessage}
          onCopyRoomCode={copyRoomCode}
          onShareGame={shareGame}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LobbyPlayerList game={game} />

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Mode Soirée — info block */}
            {game.is_party_mode && (
              <div className="card border-2 border-primary-200 bg-primary-50">
                <div className="flex items-start gap-3">
                  <span className="text-3xl">🎉</span>
                  <div>
                    <h3 className="font-bold text-primary-800 mb-1">Mode Soirée activé</h3>
                    {isHost ? (
                      <p className="text-sm text-primary-700">
                        Vous êtes <strong>hôte spectateur</strong>. Projetez cet écran sur grand écran — il affichera la musique
                        et le classement. Les joueurs n'auront sur leur téléphone que les boutons de réponse.
                      </p>
                    ) : (
                      <p className="text-sm text-primary-700">
                        La musique jouera depuis l'écran projeté. Sur votre téléphone vous verrez
                        <strong> uniquement les boutons de réponse</strong>.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
            {/* Playlist Selection — hidden for karaoke (single track pre-selected) */}
            {game.mode !== 'karaoke' && (
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
                  {(selectedPlaylist?.image_url || game.playlist_image_url) && (
                    <img
                      src={selectedPlaylist?.image_url || game.playlist_image_url}
                      alt={selectedPlaylist?.name || game.playlist_name || 'Playlist'}
                      className="w-20 h-20 rounded-md object-cover"
                    />
                  )}
                  <div>
                    <h3 className="font-semibold">
                      {selectedPlaylist?.name || game.playlist_name || 'Playlist sélectionnée'}
                    </h3>
                    {(selectedPlaylist || game.playlist_name) && (
                      <p className="text-sm text-gray-600">
                        {selectedPlaylist
                          ? `${selectedPlaylist.total_tracks} morceaux • ${selectedPlaylist.owner}`
                          : game.playlist_name ? `Playlist Deezer #${game.playlist_id}` : ''}
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
            )}

            <LobbyActions
              game={game}
              isHost={isHost}
              isSolo={isSolo}
              startingGame={startingGame}
              startError={startError}
              onLeave={handleLeaveGame}
              onStart={handleStartGame}
              onInvite={() => setShowInviteModal(true)}
            />
          </div>
        </div>
      </div>

      {/* Invite Friends Modal */}
      {showInviteModal && roomCode && (
        <InviteFriendsModal
          roomCode={roomCode}
          onClose={() => setShowInviteModal(false)}
        />
      )}
    </div>
  );
}
