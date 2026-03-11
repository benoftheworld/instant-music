import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import type { Game } from '../../types';
import useAsyncAction from '@/hooks/useAsyncAction';

/** Extrait le message d'erreur d'une réponse Axios. */
function extractApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const e = err as { response?: { status?: number; data?: { error?: string } } };
    if (e.response?.status === 404) return 'Partie introuvable. Vérifiez le code et réessayez.';
    if (e.response?.data?.error) return e.response.data.error;
  }
  return 'Erreur lors de la tentative de rejoindre la partie';
}

export function useJoinGamePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [roomCode, setRoomCode] = useState(searchParams.get('code') || '');

  // Public games
  const [publicGames, setPublicGames] = useState<Game[]>([]);
  const [publicLoading, setPublicLoading] = useState(true);
  const [publicSearch, setPublicSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'code' | 'public'>('public');

  const { loading, error, setError, run } = useAsyncAction();

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

  const joinByCode = (code: string) =>
    run(
      async () => {
        const game = await gameService.getGame(code);

        if (game.status === 'finished') throw new Error('Cette partie est terminée');
        if (game.status === 'in_progress') throw new Error('Cette partie est déjà en cours');
        if (game.player_count >= game.max_players) throw new Error('Cette partie est complète');

        await gameService.joinGame(game.room_code);
        navigate(`/game/lobby/${game.room_code}`);
      },
      extractApiError,
    );

  const handleJoinGame = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!roomCode.trim()) {
      setError('Veuillez entrer un code de salle');
      return;
    }

    await joinByCode(roomCode.trim().toUpperCase());
  };

  return {
    navigate,
    roomCode,
    setRoomCode,
    publicGames,
    publicLoading,
    publicSearch,
    setPublicSearch,
    activeTab,
    setActiveTab,
    loading,
    error,
    setError,
    joinByCode,
    handleJoinGame,
  };
}
