import { useEffect } from 'react';
import type { Game, User } from '@/types';
import type { GamePlayAction, RoundResults } from './useGamePlayReducer';
import { soundEffects } from '@/services/soundEffects';
import type { NavigateFunction } from 'react-router-dom';

interface UseGameWebSocketParams {
  onMessage: (event: string, callback: (data: any) => void) => () => void;
  dispatch: React.Dispatch<GamePlayAction>;
  game: Game | null;
  user: User | null;
  roomCode: string | undefined;
  navigate: NavigateFunction;
  advanceToNextRound: () => Promise<void>;
  advanceTimeoutRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  isAdvancingRef: React.MutableRefObject<boolean>;
  roundPlayingStartTimeRef: React.MutableRefObject<number>;
}

/**
 * Gère tous les messages WebSocket entrants pendant une partie.
 *
 * Dispatche les actions appropriées sur le reducer pour mettre à jour l'état
 * (round_started, round_ended, next_round, game_finished, bonus_activated).
 */
export function useGameWebSocket({
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
}: UseGameWebSocketParams): void {
  useEffect(() => {
    const unsubscribe = onMessage('message', (data: any) => {
      console.log('WebSocket message:', data);

      switch (data.type) {
        case 'round_started':
          soundEffects.roundLoading();
          dispatch({ type: 'START_ROUND', round: data.round_data });
          roundPlayingStartTimeRef.current = 0;
          // Brouillard : activer le flag ; le timer 5s démarre à ENTER_PLAYING
          if (data.round_data?.fog_active) {
            dispatch({ type: 'SET_FOG', active: true, activator: data.round_data.fog_activator ?? null });
          } else {
            dispatch({ type: 'SET_FOG', active: false, activator: null });
          }
          break;

        case 'player_answered':
          console.log('Player answered:', data.player);
          break;

        case 'round_ended': {
          const myScoreData =
            data.results?.player_scores?.[user?.username || ''];
          const wasCorrect = myScoreData?.is_correct;
          const isKaraokeMode = game?.mode === 'karaoke';

          // Play appropriate sound (skip for karaoke — no answer to judge)
          if (!isKaraokeMode) {
            if (wasCorrect) {
              soundEffects.correctAnswer();
            } else {
              soundEffects.wrongAnswer();
            }
          }

          const results: RoundResults = {
            ...data.results,
            correct_answer: data.results?.correct_answer || '',
            points_earned: myScoreData?.points_earned,
          };

          dispatch({ type: 'END_ROUND', results });

          // Update players with fresh scores from backend, preserving existing fields (e.g. avatar)
          if (data.results?.updated_players) {
            dispatch({
              type: 'UPDATE_PLAYERS',
              players: data.results.updated_players,
            });
          }

          if (isKaraokeMode) {
            // Karaoke: skip inter-round screen, go directly to final results
            // Host advances immediately; others wait for game_finished WS message
            if (user && game && game.host === user.id) {
              advanceToNextRound();
            }
          } else {
            dispatch({ type: 'ENTER_RESULTS' });
            // Host advances to next round after result display time
            const resultDisplayTime =
              (game?.score_display_duration || 10) * 1000;
            if (user && game && game.host === user.id) {
              // Annuler tout timeout précédent avant d'en reprogrammer un —
              // évite le double appel si round_ended est reçu deux fois.
              if (advanceTimeoutRef.current)
                clearTimeout(advanceTimeoutRef.current);
              advanceTimeoutRef.current = setTimeout(() => {
                advanceTimeoutRef.current = null;
                advanceToNextRound();
              }, resultDisplayTime);
            }
          }
          break;
        }

        case 'next_round':
          soundEffects.roundLoading();
          // Annuler le timeout en attente : le round suivant est déjà lancé.
          if (advanceTimeoutRef.current) {
            clearTimeout(advanceTimeoutRef.current);
            advanceTimeoutRef.current = null;
          }
          isAdvancingRef.current = false;
          dispatch({ type: 'START_ROUND', round: data.round_data });
          roundPlayingStartTimeRef.current = 0;
          // Brouillard : activer le flag ; le timer 5s démarre à ENTER_PLAYING
          if (data.round_data?.fog_active) {
            dispatch({ type: 'SET_FOG', active: true, activator: data.round_data.fog_activator ?? null });
          } else {
            dispatch({ type: 'SET_FOG', active: false, activator: null });
          }
          // Update players with fresh scores (preserving avatar)
          if (data.updated_players) {
            dispatch({
              type: 'UPDATE_PLAYERS',
              players: data.updated_players,
            });
          }
          break;

        case 'game_finished':
          soundEffects.gameFinished();
          navigate(`/game/${roomCode}/results`);
          break;

        case 'bonus_activated': {
          const bonus = data.bonus;
          // time_bonus — synchroniser la durée du round pour tous les joueurs
          if (bonus?.bonus_type === 'time_bonus' && data.new_duration) {
            dispatch({
              type: 'UPDATE_ROUND_DURATION',
              duration: data.new_duration,
            });
          }
          // steal — mettre à jour les scores affichés
          if (data.updated_players) {
            dispatch({
              type: 'UPDATE_PLAYERS',
              players: data.updated_players,
            });
          }
          break;
        }
      }
    });

    return unsubscribe;
  }, [
    onMessage,
    navigate,
    roomCode,
    user,
    game,
    advanceToNextRound,
    dispatch,
    advanceTimeoutRef,
    isAdvancingRef,
    roundPlayingStartTimeRef,
  ]);
}
