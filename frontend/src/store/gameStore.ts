import { create } from 'zustand';
import type { Game } from '@/types';

interface GameState {
  currentGame: Game | null;
  setCurrentGame: (game: Game | null) => void;
  updateGame: (game: Partial<Game>) => void;
}

export const useGameStore = create<GameState>((set) => ({
  currentGame: null,

  setCurrentGame: (game) => {
    set({ currentGame: game });
  },

  updateGame: (gameUpdate) => {
    set((state) => ({
      currentGame: state.currentGame
        ? { ...state.currentGame, ...gameUpdate }
        : null,
    }));
  },
}));
