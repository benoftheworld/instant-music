import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { gameService } from '@/services/gameService';
import { api } from '@/services/api';
import { createGame, createGamePlayer, createGameHistory, createCreateGameData, createKaraokeSong } from '@/tests/shared/factories';

class GameServiceTest extends BaseServiceTest {
  protected name = 'gameService';

  run() {
    describe('gameService', () => {
      this.setup(api);

      this.testGetGameHistory();
      this.testGetGameHistoryWithMode();
      this.testGetRecentGames();
      this.testGetTopPlayers();
      this.testGetTopPlayersArray();
      this.testCreateGame();
      this.testGetGame();
      this.testUpdateGame();
      this.testJoinGame();
      this.testLeaveGame();
      this.testStartGame();
      this.testGetPublicGames();
      this.testGetCurrentRound();
      this.testSubmitAnswer();
      this.testEndRound();
      this.testNextRound();
      this.testGetResults();
      this.testListKaraokeSongs();
      this.testListKaraokeSongsPaginated();
      this.testGetGameError();
    });
  }

  private testGetGameHistory() {
    it('getGameHistory — succès paginé', async () => {
      const history = [createGameHistory()];
      this.mockGet('/games/history/', { results: history, count: 1 });
      const result = await gameService.getGameHistory(1, 20);
      expect(result.results).toEqual(history);
      expect(result.count).toBe(1);
    });
  }

  private testGetGameHistoryWithMode() {
    it('getGameHistory — avec filtre mode', async () => {
      this.mockGet('/games/history/', { results: [], count: 0 });
      await gameService.getGameHistory(1, 20, 'classique');
      expect(api.get).toHaveBeenCalledWith('/games/history/', {
        params: { page: 1, page_size: 20, mode: 'classique' },
      });
    });
  }

  private testGetRecentGames() {
    it('getRecentGames — succès', async () => {
      const history = [createGameHistory()];
      this.mockGet('/games/history/', { results: history, count: 1 });
      const result = await gameService.getRecentGames(5);
      expect(result).toEqual(history);
    });
  }

  private testGetTopPlayers() {
    it('getTopPlayers — format paginé', async () => {
      const entries = [{ rank: 1, username: 'alice' }];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { results: entries } });
      const result = await gameService.getTopPlayers(5);
      expect(result).toEqual(entries);
    });
  }

  private testGetTopPlayersArray() {
    it('getTopPlayers — format array', async () => {
      const entries = [{ rank: 1, username: 'alice' }];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: entries });
      const result = await gameService.getTopPlayers(5);
      expect(result).toEqual(entries);
    });
  }

  private testCreateGame() {
    it('createGame — succès', async () => {
      const data = createCreateGameData();
      const game = createGame();
      this.mockPost('/games/', game);
      const result = await gameService.createGame(data);
      expect(result).toEqual(game);
    });
  }

  private testGetGame() {
    it('getGame — succès', async () => {
      const game = createGame({ room_code: 'ABC123' });
      this.mockGet('/games/ABC123/', game);
      const result = await gameService.getGame('ABC123');
      expect(result).toEqual(game);
    });
  }

  private testUpdateGame() {
    it('updateGame — succès', async () => {
      const game = createGame({ room_code: 'ABC123' });
      this.mockPatch('/games/ABC123/', game);
      const result = await gameService.updateGame('ABC123', { num_rounds: 5 });
      expect(result).toEqual(game);
    });
  }

  private testJoinGame() {
    it('joinGame — succès', async () => {
      const player = createGamePlayer();
      this.mockPost('/games/ABC123/join/', player);
      const result = await gameService.joinGame('ABC123');
      expect(result).toEqual(player);
    });
  }

  private testLeaveGame() {
    it('leaveGame — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await gameService.leaveGame('ABC123');
      expect(api.post).toHaveBeenCalledWith('/games/ABC123/leave/');
    });
  }

  private testStartGame() {
    it('startGame — succès', async () => {
      const game = createGame({ status: 'in_progress' });
      this.mockPost('/games/ABC123/start/', game);
      const result = await gameService.startGame('ABC123');
      expect(result.status).toBe('in_progress');
    });
  }

  private testGetPublicGames() {
    it('getPublicGames — succès', async () => {
      const games = [createGame({ is_public: true })];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { results: games } });
      const result = await gameService.getPublicGames();
      expect(result).toEqual(games);
    });
  }

  private testGetCurrentRound() {
    it('getCurrentRound — succès', async () => {
      const response = { current_round: null, message: 'Attente' };
      this.mockGet('/games/ABC123/current-round/', response);
      const result = await gameService.getCurrentRound('ABC123');
      expect(result.current_round).toBeNull();
    });
  }

  private testSubmitAnswer() {
    it('submitAnswer — succès', async () => {
      const response = { id: 1, is_correct: true, points_earned: 100 };
      this.mockPost('/games/ABC123/answer/', response);
      const result = await gameService.submitAnswer('ABC123', { answer: 'Daft Punk', response_time: 3.5 });
      expect(result.is_correct).toBe(true);
    });
  }

  private testEndRound() {
    it('endCurrentRound — succès', async () => {
      const response = { message: 'Round terminé.', correct_answer: 'Artist' };
      this.mockPost('/games/ABC123/end-round/', response);
      const result = await gameService.endCurrentRound('ABC123');
      expect(result.message).toBeTruthy();
    });
  }

  private testNextRound() {
    it('nextRound — succès', async () => {
      this.mockPost('/games/ABC123/next-round/', { message: 'ok' });
      const result = await gameService.nextRound('ABC123');
      expect(result.message).toBeTruthy();
    });
  }

  private testGetResults() {
    it('getResults — succès', async () => {
      const results = { game: createGame(), rankings: [], rounds: [] };
      this.mockGet('/games/ABC123/results/', results);
      const result = await gameService.getResults('ABC123');
      expect(result.game).toBeDefined();
    });
  }

  private testListKaraokeSongs() {
    it('listKaraokeSongs — format array', async () => {
      const songs = [createKaraokeSong()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: songs });
      const result = await gameService.listKaraokeSongs();
      expect(result).toEqual(songs);
    });
  }

  private testListKaraokeSongsPaginated() {
    it('listKaraokeSongs — format paginé', async () => {
      const songs = [createKaraokeSong()];
      (api.get as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({ data: { results: songs, next: null } });
      const result = await gameService.listKaraokeSongs();
      expect(result).toEqual(songs);
    });
  }

  private testGetGameError() {
    it('getGame — erreur 404', async () => {
      this.mockError('get', 404, { detail: 'Introuvable.' });
      await expect(gameService.getGame('NOPE')).rejects.toThrow();
    });
  }
}

new GameServiceTest().run();
