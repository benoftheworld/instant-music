import { api } from './api';
import type { Game, CreateGameData, GamePlayer, GameRound, KaraokeSong } from '@/types';

// ── Response types for game API endpoints ────────────────────────────────

export interface CurrentRoundResponse {
  current_round: GameRound | null;
  next_round?: GameRound;
  message?: string;
}

export interface SubmitAnswerResponse {
  id: number;
  round: number;
  player: number;
  answer: string;
  is_correct: boolean;
  points_earned: number;
  response_time: number;
  answered_at: string;
}

export interface EndRoundResponse {
  message: string;
  correct_answer?: string;
}

export interface NextRoundResponse {
  // Either a GameRound (next round started) or a game-finished payload
  game?: Game;
  message?: string;
}

export interface GameResults {
  game: Game & {
    mode_display: string;
    answer_mode_display: string;
    guess_target_display: string;
  };
  rankings: GamePlayer[];
  rounds: unknown[];
}

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

  async leaveGame(roomCode: string): Promise<void> {
    await api.post(`/games/${roomCode}/leave/`);
  },

  async startGame(roomCode: string): Promise<Game> {
    const response = await api.post<Game>(`/games/${roomCode}/start/`);
    return response.data;
  },

  async getPublicGames(search?: string): Promise<Game[]> {
    const params = search ? { search } : {};
    const response = await api.get<{ results: Game[] }>('/games/public/', { params });
    return response.data.results;
  },

  async getCurrentRound(roomCode: string): Promise<CurrentRoundResponse> {
    const response = await api.get<CurrentRoundResponse>(`/games/${roomCode}/current-round/`);
    return response.data;
  },

  async submitAnswer(roomCode: string, data: { answer: string; response_time: number }): Promise<SubmitAnswerResponse> {
    const response = await api.post<SubmitAnswerResponse>(`/games/${roomCode}/answer/`, data);
    return response.data;
  },

  async endCurrentRound(roomCode: string): Promise<EndRoundResponse> {
    const response = await api.post<EndRoundResponse>(`/games/${roomCode}/end-round/`);
    return response.data;
  },

  async nextRound(roomCode: string): Promise<NextRoundResponse> {
    const response = await api.post<NextRoundResponse>(`/games/${roomCode}/next-round/`);
    return response.data;
  },

  async getResults(roomCode: string): Promise<GameResults> {
    const response = await api.get<GameResults>(`/games/${roomCode}/results/`);
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
      const response = await api.get(url) as { data: unknown };
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
