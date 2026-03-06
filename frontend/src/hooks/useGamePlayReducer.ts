import type { Game, GamePlayer, GameRound } from '@/types';
import { mergeUpdatedPlayers } from '@/utils/mergeUpdatedPlayers';

// ── Types ───────────────────────────────────────────────────────────────────

export type RoundPhase = 'loading' | 'playing' | 'results';

export interface PlayerScore {
  is_correct: boolean;
  points_earned: number;
  response_time: number;
  streak_bonus?: number;
  consecutive_correct?: number;
}

export interface RoundResults {
  correct_answer: string;
  player_scores?: Record<string, PlayerScore>;
  points_earned?: number;
}

export interface GamePlayState {
  game: Game | null;
  currentRound: GameRound | null;
  timeRemaining: number;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
  loading: boolean;
  myPointsEarned: number;
  excludedOptions: string[];
  roundPhase: RoundPhase;
  fogActive: boolean;
  fogActivator: string | null;
}

export type GamePlayAction =
  | { type: 'SET_GAME'; game: Game }
  | { type: 'UPDATE_PLAYERS'; players: Partial<GamePlayer>[] }
  | { type: 'LOADING_DONE' }
  | { type: 'START_ROUND'; round: GameRound }
  | { type: 'ENTER_PLAYING' }
  | { type: 'SUBMIT_ANSWER'; answer: string }
  | { type: 'SET_POINTS_EARNED'; points: number }
  | { type: 'END_ROUND'; results: RoundResults }
  | { type: 'ENTER_RESULTS' }
  | { type: 'TICK'; time: number }
  | { type: 'SET_EXCLUDED_OPTIONS'; options: string[] }
  | { type: 'UPDATE_ROUND_DURATION'; duration: number }
  | { type: 'SET_FOG'; active: boolean; activator: string | null };

// ── Initial state ───────────────────────────────────────────────────────────

export const initialGamePlayState: GamePlayState = {
  game: null,
  currentRound: null,
  timeRemaining: 0,
  hasAnswered: false,
  selectedAnswer: null,
  showResults: false,
  roundResults: null,
  loading: true,
  myPointsEarned: 0,
  excludedOptions: [],
  roundPhase: 'loading',
  fogActive: false,
  fogActivator: null,
};

// ── Reducer ─────────────────────────────────────────────────────────────────

export function gamePlayReducer(
  state: GamePlayState,
  action: GamePlayAction,
): GamePlayState {
  switch (action.type) {
    case 'SET_GAME':
      return { ...state, game: action.game };

    case 'UPDATE_PLAYERS':
      if (!state.game) return state;
      return {
        ...state,
        game: {
          ...state.game,
          players: mergeUpdatedPlayers(state.game.players, action.players),
        },
      };

    case 'LOADING_DONE':
      return { ...state, loading: false };

    case 'START_ROUND':
      return {
        ...state,
        currentRound: action.round,
        timeRemaining: action.round.duration,
        hasAnswered: false,
        selectedAnswer: null,
        showResults: false,
        roundResults: null,
        myPointsEarned: 0,
        excludedOptions: [],
        roundPhase: 'loading',
      };

    case 'ENTER_PLAYING':
      return { ...state, roundPhase: 'playing' };

    case 'SUBMIT_ANSWER':
      return { ...state, hasAnswered: true, selectedAnswer: action.answer };

    case 'SET_POINTS_EARNED':
      return { ...state, myPointsEarned: action.points };

    case 'END_ROUND': {
      // Use server-provided points_earned, with client-cached myPointsEarned as fallback
      const results = {
        ...action.results,
        points_earned: action.results.points_earned ?? state.myPointsEarned,
      };
      return { ...state, showResults: true, roundResults: results };
    }

    case 'ENTER_RESULTS':
      return { ...state, roundPhase: 'results' };

    case 'TICK':
      return { ...state, timeRemaining: action.time };

    case 'SET_EXCLUDED_OPTIONS':
      return { ...state, excludedOptions: action.options };

    case 'UPDATE_ROUND_DURATION':
      if (!state.currentRound) return state;
      return {
        ...state,
        currentRound: { ...state.currentRound, duration: action.duration },
      };

    case 'SET_FOG':
      return { ...state, fogActive: action.active, fogActivator: action.activator };

    default:
      return state;
  }
}
