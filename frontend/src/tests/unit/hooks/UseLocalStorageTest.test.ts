import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useLocalStorage from '@/hooks/useLocalStorage';

class UseLocalStorageTest {
  run() {
    describe('useLocalStorage', () => {
      beforeEach(() => {
        localStorage.clear();
      });

      this.testInitialValue();
      this.testPersistsToLocalStorage();
      this.testReadsExistingValue();
      this.testFunctionalUpdate();
      this.testRemovesOnNull();
      this.testHandlesNonJsonString();
    });
  }

  private testInitialValue() {
    it('retourne la valeur initiale si localStorage vide', () => {
      const { result } = renderHook(() => useLocalStorage('key', 42));
      expect(result.current[0]).toBe(42);
    });
  }

  private testPersistsToLocalStorage() {
    it('persiste la valeur dans localStorage', () => {
      const { result } = renderHook(() => useLocalStorage('key', ''));
      act(() => result.current[1]('hello'));
      expect(result.current[0]).toBe('hello');
      expect(localStorage.getItem('key')).toBe('"hello"');
    });
  }

  private testReadsExistingValue() {
    it('lit une valeur existante', () => {
      localStorage.setItem('existing', JSON.stringify({ a: 1 }));
      const { result } = renderHook(() => useLocalStorage('existing', {}));
      expect(result.current[0]).toEqual({ a: 1 });
    });
  }

  private testFunctionalUpdate() {
    it('supporte les mises à jour fonctionnelles', () => {
      const { result } = renderHook(() => useLocalStorage('count', 0));
      act(() => result.current[1]((prev) => prev + 1));
      expect(result.current[0]).toBe(1);
    });
  }

  private testRemovesOnNull() {
    it('supprime la clé si la valeur est null', () => {
      localStorage.setItem('rm', '"data"');
      const { result } = renderHook(() => useLocalStorage<string | null>('rm', null));
      act(() => result.current[1](null));
      expect(localStorage.getItem('rm')).toBeNull();
    });
  }

  private testHandlesNonJsonString() {
    it('retourne la chaîne brute si non-JSON', () => {
      localStorage.setItem('raw', 'not-json');
      const { result } = renderHook(() => useLocalStorage('raw', 'default'));
      expect(result.current[0]).toBe('not-json');
    });
  }
}

new UseLocalStorageTest().run();
