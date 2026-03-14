import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import usePagination from '@/hooks/usePagination';

class UsePaginationTest {
  run() {
    describe('usePagination', () => {
      this.testDefaults();
      this.testCustomPageSize();
      this.testGoNext();
      this.testGoPrev();
      this.testTotalPages();
      this.testHasNextHasPrev();
      this.testReset();
      this.testSetPage();
    });
  }

  private testDefaults() {
    it('valeurs par défaut — page 1, pageSize 20', () => {
      const { result } = renderHook(() => usePagination());
      expect(result.current.page).toBe(1);
      expect(result.current.pageSize).toBe(20);
      expect(result.current.totalCount).toBeNull();
      expect(result.current.totalPages).toBeNull();
    });
  }

  private testCustomPageSize() {
    it('pageSize custom', () => {
      const { result } = renderHook(() => usePagination(50));
      expect(result.current.pageSize).toBe(50);
    });
  }

  private testGoNext() {
    it('goNext — incrémente la page quand hasNext', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(30));
      act(() => result.current.goNext());
      expect(result.current.page).toBe(2);
    });
  }

  private testGoPrev() {
    it('goPrev — décrémente la page quand hasPrev', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(30));
      act(() => result.current.goNext()); // page 2
      act(() => result.current.goPrev());
      expect(result.current.page).toBe(1);
    });
  }

  private testTotalPages() {
    it('totalPages — calcule correctement', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(25));
      expect(result.current.totalPages).toBe(3);
    });
  }

  private testHasNextHasPrev() {
    it('hasNext/hasPrev — bornes correctes', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(20));
      // page 1 of 2
      expect(result.current.hasNext).toBe(true);
      expect(result.current.hasPrev).toBe(false);
      act(() => result.current.goNext()); // page 2
      expect(result.current.hasNext).toBe(false);
      expect(result.current.hasPrev).toBe(true);
    });
  }

  private testReset() {
    it('reset — revient à page 1 et totalCount null', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(50));
      act(() => result.current.goNext());
      act(() => result.current.reset());
      expect(result.current.page).toBe(1);
      expect(result.current.totalCount).toBeNull();
    });
  }

  private testSetPage() {
    it('setPage — saute directement à une page', () => {
      const { result } = renderHook(() => usePagination(10));
      act(() => result.current.setTotalCount(100));
      act(() => result.current.setPage(5));
      expect(result.current.page).toBe(5);
    });
  }
}

new UsePaginationTest().run();
