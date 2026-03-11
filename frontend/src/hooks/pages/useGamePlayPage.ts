import { useEffect, useReducer, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../store/authStore';
import {
  gamePlayReducer,
  initialGamePlayState,
} from '../../hooks/useGamePlayReducer';
import { useGameTimer } from '../../hooks/useGameTimer';
import { useGameWebSocket } from '../../hooks/useGameWebSocket';

export function useGamePlayPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  // ── State (single reducer instead of 11 useState) ──────────────────────
  const [state, dispatch] = useReducer(gamePlayReducer, initialGamePlayState);
  const {
    game,
    currentRound,
    timeRemaining,
    hasAnswered,
    selectedAnswer,
    showResults,
    roundResults,
    loading,
    myPointsEarned,
    excludedOptions,
    roundPhase,
    fogActive,
    fogActivator,
    loadingDuration,
  } = state;

  // ── Refs (imperative / timing concerns) ────────────────────────────────
  const isAdvancingRef = useRef(false);
  const advanceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const roundPlayingStartTimeRef = useRef<number>(0);

  // ── WebSocket connection ───────────────────────────────────────────────
  const { sendMessage, onMessage } = useWebSocket(roomCode || '');

  // ── Data loading ───────────────────────────────────────────────────────

  const loadCurrentRound = useCallback(async () => {
    if (!roomCode) return;

    try {
      const response = await gameService.getCurrentRound(roomCode);

      if (response.current_round) {
        const round = response.current_round;
        dispatch({ type: 'START_ROUND', round });
        roundPlayingStartTimeRef.current = 0;

        if (round.started_at) {
          const elapsedMs = Math.max(0, Date.now() - new Date(round.started_at).getTime());
          const countdownMs = (game?.timer_start_round || 5) * 1000;

          if (elapsedMs >= countdownMs) {
            roundPlayingStartTimeRef.current = new Date(round.started_at).getTime() + countdownMs;
            dispatch({ type: 'ENTER_PLAYING' });
          } else {
            const remainingSec = Math.max(1, Math.ceil((countdownMs - elapsedMs) / 1000));
            dispatch({ type: 'SET_LOADING_DURATION', duration: remainingSec });
          }
        }
      } else if (response.message === 'Partie terminée') {
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load round:', error);
    } finally {
      dispatch({ type: 'LOADING_DONE' });
    }
  }, [roomCode, navigate, game?.timer_start_round]);

  const loadGame = useCallback(async () => {
    if (!roomCode) return;

    try {
      const gameData = await gameService.getGame(roomCode);
      dispatch({ type: 'SET_GAME', game: gameData });

      if (gameData.status === 'finished') {
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load game:', error);
    }
  }, [roomCode, navigate]);

  const advanceToNextRound = useCallback(async () => {
    if (isAdvancingRef.current || !roomCode) return;
    isAdvancingRef.current = true;
    if (advanceTimeoutRef.current) {
      clearTimeout(advanceTimeoutRef.current);
      advanceTimeoutRef.current = null;
    }
    try {
      await gameService.nextRound(roomCode);
    } catch (error) {
      console.error('Failed to advance to next round:', error);
    } finally {
      setTimeout(() => { isAdvancingRef.current = false; }, 3000);
    }
  }, [roomCode]);

  // ── Extracted hooks ────────────────────────────────────────────────────

  useGameTimer({
    currentRound,
    showResults,
    roundPhase,
    game,
    roomCode,
    user,
    roundPlayingStartTimeRef,
    dispatch,
  });

  useGameWebSocket({
    onMessage,
    dispatch,
    game,
    user,
    roomCode,
    navigate,
    advanceToNextRound,
    advanceTimeoutRef,
    isAdvancingRef,
    roundPlayingStartTimeRef,
  });

  useEffect(() => {
    return () => {
      if (advanceTimeoutRef.current) {
        clearTimeout(advanceTimeoutRef.current);
        advanceTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    loadGame();
    loadCurrentRound();
  }, [loadGame, loadCurrentRound]);

  // ── Handlers ───────────────────────────────────────────────────────────

  const handleAnswerSubmit = async (answer: string) => {
    if (!roomCode || !currentRound || hasAnswered) return;
    if (game?.mode === 'karaoke') return;
    if (game?.is_party_mode && user?.id === game?.host) return;

    soundEffects.answerSubmitted();
    dispatch({ type: 'SUBMIT_ANSWER', answer });

    const responseTime = roundPlayingStartTimeRef.current > 0
      ? Math.max(0, (Date.now() - roundPlayingStartTimeRef.current) / 1000)
      : Math.max(0, currentRound.duration - timeRemaining);

    try {
      const answerResult = await gameService.submitAnswer(roomCode, {
        answer,
        response_time: responseTime
      });

      dispatch({ type: 'SET_POINTS_EARNED', points: answerResult.points_earned || 0 });

      sendMessage({
        type: 'player_answer',
        player: user?.username || 'You',
        answer: answer,
        response_time: responseTime
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleLoadingComplete = () => {
    soundEffects.countdownGo();
    roundPlayingStartTimeRef.current = Date.now();
    dispatch({ type: 'ENTER_PLAYING' });
    if (fogActive) {
      setTimeout(() => dispatch({ type: 'SET_FOG', active: false, activator: null }), 5000);
    }
  };

  const handleKaraokeEnded = () => {
    if (user && game && game.host === user.id && !showResults) {
      gameService.endCurrentRound(roomCode!)
        .catch(err => console.error('Failed to end karaoke round:', err));
    }
  };

  const getTextPlaceholder = () => {
    switch (currentRound?.question_type) {
      case 'guess_artist': return 'Nom de l\'artiste...';
      case 'blind_inverse': return 'Titre du morceau...';
      case 'lyrics': return 'Le mot manquant...';
      default: return 'Titre du morceau...';
    }
  };

  const isKaraoke = game?.mode === 'karaoke';
  const isSolo = isKaraoke || !game?.is_online;
  const isTextMode = game?.answer_mode === 'text';
  const seekOffsetMs = (game?.timer_start_round || 5) * 1000;
  const currentMode = currentRound?.extra_data?.round_mode || game?.mode;

  const commonQuestionProps = currentRound ? {
    round: currentRound,
    onAnswerSubmit: handleAnswerSubmit,
    hasAnswered,
    selectedAnswer,
    showResults,
    roundResults,
    seekOffsetMs,
    excludedOptions,
    fogBlur: fogActive && fogActivator !== user?.username,
  } : null;

  // En mode soirée, exclure le présentateur (hôte) du classement
  const displayPlayers = game?.is_party_mode
    ? (game?.players || []).filter(p => String(p.user) !== String(game.host))
    : (game?.players || []);

  return {
    roomCode,
    user,
    game,
    currentRound,
    timeRemaining,
    hasAnswered,
    selectedAnswer,
    showResults,
    roundResults,
    loading,
    myPointsEarned,
    excludedOptions,
    roundPhase,
    fogActive,
    fogActivator,
    loadingDuration,
    dispatch,
    handleAnswerSubmit,
    handleLoadingComplete,
    handleKaraokeEnded,
    getTextPlaceholder,
    isKaraoke,
    isSolo,
    isTextMode,
    seekOffsetMs,
    currentMode,
    commonQuestionProps,
    displayPlayers,
  };
}
