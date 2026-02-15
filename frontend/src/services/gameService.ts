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
  
  async updateGame(roomCode: string, data: Partial<CreateGameData>): Promise<Game> {
    const response = await api.patch<Game>(`/games/${roomCode}/`, data);
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
  
  async getCurrentRound(roomCode: string): Promise<any> {
    const response = await api.get(`/games/${roomCode}/current-round/`);
    return response.data;
  },
  
  async submitAnswer(roomCode: string, data: { answer: string; response_time: number }): Promise<any> {
    const response = await api.post(`/games/${roomCode}/answer/`, data);
    return response.data;
  },
  
  async nextRound(roomCode: string): Promise<any> {
    const response = await api.post(`/games/${roomCode}/next-round/`);
    return response.data;
  },
  
  async getResults(roomCode: string): Promise<any> {
    const response = await api.get(`/games/${roomCode}/results/`);
    return response.data;
  },
};

