import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ roomCode: 'TEST' }),
    useSearchParams: () => [new URLSearchParams()],
  };
});

vi.mock('@/services/gameService', () => ({
  gameService: {
    getPublicGames: vi.fn().mockResolvedValue([]),
    getGame: vi.fn().mockResolvedValue({
      room_code: 'TEST', status: 'waiting', player_count: 2, max_players: 8,
      players: [], host: 1, mode: 'classique', is_online: true,
    }),
    joinGame: vi.fn().mockResolvedValue(undefined),
  },
}));

import { useJoinGamePage } from '@/hooks/pages/useJoinGamePage';

class UseJoinGamePageTest {
  private createWrapper() {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(MemoryRouter, null,
        React.createElement(QueryClientProvider, { client: qc }, children)
      );
  }

  run() {
    describe('useJoinGamePage', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
      });

      this.testInitialState();
      this.testHandleJoinEmptyCode();
      this.testJoinSuccess();
    });
  }

  private testInitialState() {
    it('état initial — roomCode vide, activeTab public', () => {
      const { result } = renderHook(() => useJoinGamePage(), { wrapper: this.createWrapper() });
      expect(result.current.roomCode).toBe('');
      expect(result.current.activeTab).toBe('public');
      expect(result.current.loading).toBe(false);
    });
  }

  private testHandleJoinEmptyCode() {
    it('handleJoinGame avec code vide — affiche erreur', async () => {
      const { result } = renderHook(() => useJoinGamePage(), { wrapper: this.createWrapper() });
      await act(async () => {
        await result.current.handleJoinGame({ preventDefault: vi.fn() } as any);
      });
      expect(result.current.error).toBeTruthy();
    });
  }

  private testJoinSuccess() {
    it('joinByCode — succès → navigue vers lobby', async () => {
      const { result } = renderHook(() => useJoinGamePage(), { wrapper: this.createWrapper() });
      await act(async () => {
        await result.current.joinByCode('TEST');
      });
      expect(mockNavigate).toHaveBeenCalledWith('/game/lobby/TEST');
    });
  }
}

new UseJoinGamePageTest().run();
