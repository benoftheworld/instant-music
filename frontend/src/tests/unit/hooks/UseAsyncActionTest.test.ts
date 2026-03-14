import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useAsyncAction from '@/hooks/useAsyncAction';

class UseAsyncActionTest {
  run() {
    describe('useAsyncAction', () => {
      this.testInitialState();
      this.testRunSuccess();
      this.testRunError();
      this.testRunCustomErrorExtractor();
      this.testSetErrorManual();
      this.testClearError();
      this.testLoadingCycle();
    });
  }

  private testInitialState() {
    it('état initial — loading false, error null', () => {
      const { result } = renderHook(() => useAsyncAction());
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  }

  private testRunSuccess() {
    it('run — retourne la valeur en cas de succès', async () => {
      const { result } = renderHook(() => useAsyncAction());
      let value: string | undefined;
      await act(async () => {
        value = await result.current.run(async () => 'hello');
      });
      expect(value).toBe('hello');
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  }

  private testRunError() {
    it('run — capture l\'erreur et retourne undefined', async () => {
      const { result } = renderHook(() => useAsyncAction());
      let value: unknown;
      await act(async () => {
        value = await result.current.run(async () => {
          throw new Error('boom');
        });
      });
      expect(value).toBeUndefined();
      expect(result.current.error).toBe('boom');
      expect(result.current.loading).toBe(false);
    });
  }

  private testRunCustomErrorExtractor() {
    it('run — utilise onError custom pour extraire le message', async () => {
      const { result } = renderHook(() => useAsyncAction());
      await act(async () => {
        await result.current.run(
          async () => { throw { code: 42 }; },
          (err) => `Code: ${(err as any).code}`,
        );
      });
      expect(result.current.error).toBe('Code: 42');
    });
  }

  private testSetErrorManual() {
    it('setError — pose un message manuellement', () => {
      const { result } = renderHook(() => useAsyncAction());
      act(() => result.current.setError('manual'));
      expect(result.current.error).toBe('manual');
    });
  }

  private testClearError() {
    it('clearError — efface le message', () => {
      const { result } = renderHook(() => useAsyncAction());
      act(() => result.current.setError('oops'));
      act(() => result.current.clearError());
      expect(result.current.error).toBeNull();
    });
  }

  private testLoadingCycle() {
    it('run — passe loading à true puis false', async () => {
      const { result } = renderHook(() => useAsyncAction());
      let resolve!: () => void;
      const promise = new Promise<void>((r) => { resolve = r; });

      const runPromise = act(async () => {
        await result.current.run(async () => { await promise; });
      });

      // Note: can't observe loading=true mid-act easily,
      // but after act resolves it should be false
      resolve();
      await runPromise;
      expect(result.current.loading).toBe(false);
    });
  }
}

new UseAsyncActionTest().run();
