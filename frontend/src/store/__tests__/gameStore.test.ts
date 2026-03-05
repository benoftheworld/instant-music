import { describe, it, expect, beforeEach } from 'vitest';
import { useGameStore } from '@/store/gameStore';

const mockGame = {
  id: 'game-uuid-1',
  name: 'Test Game',
  room_code: 'ABC123',
  host_username: 'host',
  mode: 'classique' as const,
  status: 'waiting' as const,
  max_players: 8,
  num_rounds: 10,
  players: [],
  player_count: 1,
  created_at: '2024-01-01T00:00:00Z',
};

describe('gameStore', () => {
  beforeEach(() => {
    useGameStore.setState({ currentGame: null });
  });

  it('etat initial sans partie', () => {
    const state = useGameStore.getState();
    expect(state.currentGame).toBeNull();
  });

  it('setCurrentGame definit la partie courante', () => {
    useGameStore.getState().setCurrentGame(mockGame as any);

    const state = useGameStore.getState();
    expect(state.currentGame).toEqual(mockGame);
  });

  it('setCurrentGame a null reinitialise', () => {
    useGameStore.getState().setCurrentGame(mockGame as any);
    useGameStore.getState().setCurrentGame(null);

    expect(useGameStore.getState().currentGame).toBeNull();
  });

  it('updateGame met a jour partiellement la partie', () => {
    useGameStore.getState().setCurrentGame(mockGame as any);
    useGameStore.getState().updateGame({ status: 'in_progress' as any });

    const state = useGameStore.getState();
    expect(state.currentGame?.status).toBe('in_progress');
    expect(state.currentGame?.room_code).toBe('ABC123');
  });

  it('updateGame sans partie courante ne crash pas', () => {
    useGameStore.getState().updateGame({ status: 'in_progress' as any });
    expect(useGameStore.getState().currentGame).toBeNull();
  });
});
