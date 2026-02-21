import { api } from './api';
import type { Game, CreateGameData, GamePlayer, KaraokeSong } from '@/types';

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

  async endCurrentRound(roomCode: string): Promise<any> {
    const response = await api.post(`/games/${roomCode}/end-round/`);
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

  async downloadResultsPdf(roomCode: string): Promise<void> {
    const response = await api.get(`/games/${roomCode}/results/pdf/`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `instantmusic_resultats_${roomCode}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /** Fetch the admin-curated karaoke song catalogue (all pages). */
  async listKaraokeSongs(): Promise<KaraokeSong[]> {
    const allSongs: KaraokeSong[] = [];
    let url: string | null = '/games/karaoke-songs/';
    while (url) {
      const response: Awaited<ReturnType<typeof api.get>> = await api.get(url);
      const data: unknown = response.data;
      if (Array.isArray(data)) {
        // pagination_class = None → plain array, done
        return data as KaraokeSong[];
      }
      const paginated = data as { results?: unknown[]; next?: string | null };
      if (Array.isArray(paginated?.results)) {
        allSongs.push(...(paginated.results as KaraokeSong[]));
        // Follow DRF `next` link if present (strip base URL to keep relative)
        if (paginated.next) {
          try {
            const nextUrl: URL = new URL(paginated.next);
            url = nextUrl.pathname + nextUrl.search;
          } catch {
            url = paginated.next;
          }
        } else {
          url = null;
        }
      } else {
        url = null;
      }
    }
    return allSongs;
  },
};
