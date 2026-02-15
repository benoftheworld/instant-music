import { api } from './api';
import type { Game, CreateGameData, GamePlayer } from '@/types';

export const gameService = {
  async createGame(data: CreateGameData): Promise<Game> {
    const response = await api.post<Game>('/games/', data);
    return response.data;
  },

  async getGame(roomCode: string): Promise<Game> {
    const response = await api.get<Game>(`/games/${roomCode}/`);
    return response.data;
  },

  async joinGame(roomCode: string): Promise<GamePlayer> {
    const response = await api.post<GamePlayer>(`/games/${roomCode}/join/`);
    return response.data;
  },

  async startGame(roomCode: string): Promise<Game> {
    const response = await api.post<Game>(`/games/${roomCode}/start/`);
    return response.data;
  },

  async getAvailableGames(): Promise<Game[]> {
    const response = await api.get<Game[]>('/games/available/');
    return response.data;
  },
};
