import { useEffect } from 'react';
import type { Game, GameRound, User } from '@/types';
import type { RoundPhase, GamePlayAction } from './useGamePlayReducer';
import { gameService } from '@/services/gameService';
import { soundEffects } from '@/services/soundEffects';

interface UseGameTimerParams {
  currentRound: GameRound | null;
  showResults: boolean;
  roundPhase: RoundPhase;
  game: Game | null;
  roomCode: string | undefined;
  user: User | null;
  roundPlayingStartTimeRef: React.MutableRefObject<number>;
  dispatch: React.Dispatch<GamePlayAction>;
}

/**
 * Gère le compte à rebours du round en cours.
 *
 * - Met à jour timeRemaining toutes les 100 ms
 * - Joue les effets sonores de fin de timer
 * - L'hôte termine automatiquement le round quand le timer atteint 0
 */
export function useGameTimer({
  currentRound,
  showResults,
  roundPhase,
  game,
  roomCode,
  user,
  roundPlayingStartTimeRef,
  dispatch,
}: UseGameTimerParams): void {
  useEffect(() => {
    if (!currentRound || showResults || roundPhase !== 'playing') return;

    const calculateTimeRemaining = () => {
      // Use client-side elapsed time from the moment the playing phase started.
      // This is immune to server-client clock drift (common with Docker/WSL2 after suspend/resume).
      if (roundPlayingStartTimeRef.current > 0) {
        const elapsed = Math.floor(
          (Date.now() - roundPlayingStartTimeRef.current) / 1000,
        );
        return Math.max(0, currentRound.duration - elapsed);
      }
      return currentRound.duration;
    };

    // Update immediately
    const remaining = calculateTimeRemaining();
    dispatch({ type: 'TICK', time: remaining });
    let lastSecond = remaining;

    // Update every 1000ms — we display whole seconds so sub-second precision is unnecessary
    const interval = setInterval(() => {
      const newRemaining = calculateTimeRemaining();
      dispatch({ type: 'TICK', time: newRemaining });

      // Sound effects for countdown (disabled in karaoke — no timer UX)
      if (
        game?.mode !== 'karaoke' &&
        newRemaining !== lastSecond &&
        newRemaining > 0
      ) {
        if (newRemaining <= 3) {
          soundEffects.timerWarning();
        } else if (newRemaining <= 5) {
          soundEffects.timerTick();
        }
        lastSecond = newRemaining;
      }

      if (newRemaining <= 0) {
        clearInterval(interval);

        // In karaoke mode the round is driven by the YouTube video end event,
        // not the timer — skip the automatic termination here.
        if (game?.mode === 'karaoke') return;

        soundEffects.timeUp();

        // Host terminates the round immediately to send results to all players
        if (user && game && game.host === user.id) {
          gameService
            .endCurrentRound(roomCode!)
            .then(() => {
              console.log('Round ended by timer');
            })
            .catch((err) => {
              console.error('Failed to end round:', err);
              // Fallback: show local results if backend call fails
              dispatch({ type: 'END_ROUND', results: { correct_answer: '' } });
              dispatch({ type: 'ENTER_RESULTS' });
            });
        }
        // Non-hosts: wait for round_ended message from WebSocket
      }
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [currentRound, showResults, roundPhase, game, roomCode, user, roundPlayingStartTimeRef, dispatch]);
}
