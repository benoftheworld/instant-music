import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  gamePlayReducer,
  initialGamePlayState,
  type GamePlayState,
  type GamePlayAction,
} from '@/hooks/useGamePlayReducer';
import { createGame, createGameRound, createGamePlayer } from '@/tests/shared/factories';

class UseGamePlayReducerTest {
  private state!: GamePlayState;

  run() {
    describe('gamePlayReducer', () => {
      beforeEach(() => {
        this.state = { ...initialGamePlayState };
      });

      this.testSetGame();
      this.testUpdatePlayers();
      this.testUpdatePlayersNoGame();
      this.testLoadingDone();
      this.testStartRound();
      this.testEnterPlaying();
      this.testSubmitAnswer();
      this.testSetPointsEarned();
      this.testEndRound();
      this.testEnterReveal();
      this.testEnterResults();
      this.testTick();
      this.testSetExcludedOptions();
      this.testUpdateRoundDuration();
      this.testSetFog();
      this.testSetLoadingDuration();
      this.testDefaultReturnsState();
    });
  }

  private dispatch(action: GamePlayAction): GamePlayState {
    return gamePlayReducer(this.state, action);
  }

  private testSetGame() {
    it('SET_GAME — assigne le game', () => {
      const game = createGame();
      const next = this.dispatch({ type: 'SET_GAME', game });
      expect(next.game).toEqual(game);
    });
  }

  private testUpdatePlayers() {
    it('UPDATE_PLAYERS — fusionne les joueurs', () => {
      const player = createGamePlayer({ username: 'alice', score: 10 });
      this.state = { ...this.state, game: createGame({ players: [player] }) };
      const next = gamePlayReducer(this.state, {
        type: 'UPDATE_PLAYERS',
        players: [{ id: player.id, username: 'alice', score: 20 }],
      });
      expect(next.game!.players[0].score).toBe(20);
    });
  }

  private testUpdatePlayersNoGame() {
    it('UPDATE_PLAYERS — sans game, retourne state inchangé', () => {
      const next = this.dispatch({ type: 'UPDATE_PLAYERS', players: [] });
      expect(next).toEqual(this.state);
    });
  }

  private testLoadingDone() {
    it('LOADING_DONE — loading false', () => {
      this.state = { ...this.state, loading: true };
      const next = gamePlayReducer(this.state, { type: 'LOADING_DONE' });
      expect(next.loading).toBe(false);
    });
  }

  private testStartRound() {
    it('START_ROUND — reset l\'état de round', () => {
      const round = createGameRound({ duration: 30 });
      const next = this.dispatch({ type: 'START_ROUND', round });
      expect(next.currentRound).toEqual(round);
      expect(next.timeRemaining).toBe(30);
      expect(next.hasAnswered).toBe(false);
      expect(next.selectedAnswer).toBeNull();
      expect(next.showResults).toBe(false);
      expect(next.roundPhase).toBe('loading');
    });
  }

  private testEnterPlaying() {
    it('ENTER_PLAYING — roundPhase playing', () => {
      const next = this.dispatch({ type: 'ENTER_PLAYING' });
      expect(next.roundPhase).toBe('playing');
    });
  }

  private testSubmitAnswer() {
    it('SUBMIT_ANSWER — marque hasAnswered et selectedAnswer', () => {
      const next = this.dispatch({ type: 'SUBMIT_ANSWER', answer: 'Beatles' });
      expect(next.hasAnswered).toBe(true);
      expect(next.selectedAnswer).toBe('Beatles');
    });
  }

  private testSetPointsEarned() {
    it('SET_POINTS_EARNED — met à jour myPointsEarned', () => {
      const next = this.dispatch({ type: 'SET_POINTS_EARNED', points: 150 });
      expect(next.myPointsEarned).toBe(150);
    });
  }

  private testEndRound() {
    it('END_ROUND — montre les résultats', () => {
      this.state = { ...this.state, myPointsEarned: 50 };
      const next = gamePlayReducer(this.state, {
        type: 'END_ROUND',
        results: { correct_answer: 'Let It Be' },
      });
      expect(next.showResults).toBe(true);
      expect(next.roundResults!.correct_answer).toBe('Let It Be');
      // Uses myPointsEarned as fallback for points_earned
      expect(next.roundResults!.points_earned).toBe(50);
    });
  }

  private testEnterReveal() {
    it('ENTER_REVEAL — roundPhase reveal', () => {
      const next = this.dispatch({ type: 'ENTER_REVEAL' });
      expect(next.roundPhase).toBe('reveal');
    });
  }

  private testEnterResults() {
    it('ENTER_RESULTS — roundPhase results', () => {
      const next = this.dispatch({ type: 'ENTER_RESULTS' });
      expect(next.roundPhase).toBe('results');
    });
  }

  private testTick() {
    it('TICK — met à jour timeRemaining', () => {
      const next = this.dispatch({ type: 'TICK', time: 15 });
      expect(next.timeRemaining).toBe(15);
    });
  }

  private testSetExcludedOptions() {
    it('SET_EXCLUDED_OPTIONS — assigne excludedOptions', () => {
      const next = this.dispatch({ type: 'SET_EXCLUDED_OPTIONS', options: ['A', 'B'] });
      expect(next.excludedOptions).toEqual(['A', 'B']);
    });
  }

  private testUpdateRoundDuration() {
    it('UPDATE_ROUND_DURATION — met à jour la durée du round', () => {
      this.state = {
        ...this.state,
        currentRound: createGameRound({ duration: 30 }),
      };
      const next = gamePlayReducer(this.state, { type: 'UPDATE_ROUND_DURATION', duration: 45 });
      expect(next.currentRound!.duration).toBe(45);
    });
  }

  private testSetFog() {
    it('SET_FOG — active/désactive le brouillard', () => {
      const on = this.dispatch({ type: 'SET_FOG', active: true, activator: 'bob' });
      expect(on.fogActive).toBe(true);
      expect(on.fogActivator).toBe('bob');
      const off = gamePlayReducer(on, { type: 'SET_FOG', active: false, activator: null });
      expect(off.fogActive).toBe(false);
    });
  }

  private testSetLoadingDuration() {
    it('SET_LOADING_DURATION — assigne loadingDuration', () => {
      const next = this.dispatch({ type: 'SET_LOADING_DURATION', duration: 5 });
      expect(next.loadingDuration).toBe(5);
    });
  }

  private testDefaultReturnsState() {
    it('action inconnue — retourne state inchangé', () => {
      const next = gamePlayReducer(this.state, { type: 'UNKNOWN' } as any);
      expect(next).toEqual(this.state);
    });
  }
}

new UseGamePlayReducerTest().run();
