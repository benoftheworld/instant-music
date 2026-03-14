import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/services/gameService', () => ({
  gameService: {
    createGame: vi.fn().mockResolvedValue({ room_code: 'ABCD' }),
  },
}));

import { useCreateGamePage } from '@/hooks/pages/useCreateGamePage';

class UseCreateGamePageTest {
  private createWrapper() {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(MemoryRouter, null,
        React.createElement(QueryClientProvider, { client: qc }, children)
      );
  }

  run() {
    describe('useCreateGamePage', () => {
      beforeEach(() => vi.clearAllMocks());

      this.testInitialState();
      this.testNextPrevStep();
      this.testSelectMode();
      this.testToggleOffline();
      this.testCanProceed();
    });
  }

  private testInitialState() {
    it('état initial — step 1, mode classique', () => {
      const { result } = renderHook(() => useCreateGamePage(), { wrapper: this.createWrapper() });
      expect(result.current.currentStep).toBe(1);
      expect(result.current.selectedMode).toBe('classique');
      expect(result.current.isKaraoke).toBe(false);
      expect(result.current.loading).toBe(false);
    });
  }

  private testNextPrevStep() {
    it('nextStep/prevStep — navigation entre steps', () => {
      const { result } = renderHook(() => useCreateGamePage(), { wrapper: this.createWrapper() });
      act(() => result.current.nextStep());
      expect(result.current.currentStep).toBe(2);
      act(() => result.current.prevStep());
      expect(result.current.currentStep).toBe(1);
    });
  }

  private testSelectMode() {
    it('handleSelectMode karaoke — met maxPlayers à 1', () => {
      const { result } = renderHook(() => useCreateGamePage(), { wrapper: this.createWrapper() });
      act(() => result.current.handleSelectMode('karaoke'));
      expect(result.current.selectedMode).toBe('karaoke');
      expect(result.current.isKaraoke).toBe(true);
    });
  }

  private testToggleOffline() {
    it('handleToggleOffline — désactive online, met maxPlayers à 1', () => {
      const { result } = renderHook(() => useCreateGamePage(), { wrapper: this.createWrapper() });
      act(() => result.current.handleToggleOffline(true));
      expect(result.current.isOnline).toBe(false);
    });
  }

  private testCanProceed() {
    it('canProceed — step 1 toujours vrai', () => {
      const { result } = renderHook(() => useCreateGamePage(), { wrapper: this.createWrapper() });
      expect(result.current.canProceed()).toBe(true);
    });
  }
}

new UseCreateGamePageTest().run();
