import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { Game, YouTubePlaylist } from '../../types';
import { getApiErrorMessage } from '../../utils/apiError';

export function useGameLobbyPage() {
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
      if (data.type === 'player_joined') {
        soundEffects.playerJoined();
        if (data.game_data) {
          setGame(data.game_data);
        }
      } else if (data.type === 'player_leave') {
        if (data.game_data) {
          setGame(data.game_data);
          if (data.game_data.status === 'cancelled') {
            navigate('/');
          }
        }
      } else if (data.type === 'game_updated') {
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

      if (gameData.status === 'in_progress') {
        navigate(`/game/play/${roomCode}`);
        return;
      } else if (gameData.status === 'finished') {
        navigate('/');
        return;
      }

      if (user && gameData.host !== user.id) {
        const isAlreadyInGame = gameData.players.some((p: any) => p.user === user.id);

        if (!isAlreadyInGame) {
          try {
            await gameService.joinGame(roomCode);
            const updatedGame = await gameService.getGame(roomCode);
            setGame(updatedGame);
          } catch (joinError: any) {
            const errorMessage = joinError?.response?.data?.error;
            if (!errorMessage?.includes('déjà dans cette partie')) {
              setError('Impossible de rejoindre la partie');
            }
          }
        }
      }
    } catch (err) {
      setError('Impossible de charger la partie');
    } finally {
      setLoading(false);
    }
  }, [roomCode, user, navigate]);

  useEffect(() => {
    if (roomCode) {
      loadGame();
    }
  }, [roomCode, loadGame]);

  useEffect(() => {
    const unsubscribe = onMessage('reconnected', () => {
      loadGame();
    });
    return unsubscribe;
  }, [onMessage, loadGame]);

  const handleSelectPlaylist = async (playlist: YouTubePlaylist) => {
    if (!game || !roomCode) return;

    setSelectedPlaylist(playlist);
    setShowPlaylistSelector(false);

    try {
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

  const isHost = user?.id === game?.host;
  const isSolo = game?.mode === 'karaoke' || !game?.is_online;

  const handleStartGame = async () => {
    if (!game || !user || !roomCode || startingGame) return;

    setStartError(null);
    setStartingGame(true);

    if (game.host !== user.id) {
      setStartError('Seul l\'hôte peut démarrer la partie');
      setStartingGame(false);
      return;
    }

    if (game.mode !== 'karaoke' && !selectedPlaylist && !game.playlist_id) {
      setStartError('Veuillez sélectionner une playlist avant de démarrer');
      setShowPlaylistSelector(true);
      setStartingGame(false);
      return;
    }

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
      await gameService.startGame(roomCode);
      navigate(`/game/play/${roomCode}`);
    } catch (err: unknown) {
      console.error('Failed to start game:', err);
      const errorMessage = getApiErrorMessage(err, 'Erreur lors du démarrage de la partie');

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

  return {
    roomCode,
    game,
    loading,
    error,
    startError,
    startingGame,
    selectedPlaylist,
    showPlaylistSelector,
    setShowPlaylistSelector,
    copyMessage,
    showInviteModal,
    setShowInviteModal,
    isConnected,
    isHost,
    isSolo,
    handleSelectPlaylist,
    handleStartGame,
    handleLeaveGame,
    copyRoomCode,
    shareGame,
  };
}
