import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '@/components/layout/ErrorBoundary';

function ThrowError() {
  throw new Error('Boom');
}

class ErrorBoundaryTest {
  run() {
    describe('ErrorBoundary', () => {
      this.testRendersChildrenNormally();
      this.testShowsFallbackOnError();
      this.testDefaultFallback();
    });
  }

  private testRendersChildrenNormally() {
    it('rend les enfants sans erreur', () => {
      render(
        <ErrorBoundary>
          <div>OK</div>
        </ErrorBoundary>,
      );
      expect(screen.getByText('OK')).toBeInTheDocument();
    });
  }

  private testShowsFallbackOnError() {
    it('affiche le fallback custom en cas d\'erreur', () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
      render(
        <ErrorBoundary fallback={<div>Custom Error</div>}>
          <ThrowError />
        </ErrorBoundary>,
      );
      expect(screen.getByText('Custom Error')).toBeInTheDocument();
      spy.mockRestore();
    });
  }

  private testDefaultFallback() {
    it('affiche le fallback par défaut avec bouton recharger', () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>,
      );
      expect(screen.getByText(/quelque chose s'est mal passé/i)).toBeInTheDocument();
      expect(screen.getByText('Recharger la page')).toBeInTheDocument();
      spy.mockRestore();
    });
  }
}

new ErrorBoundaryTest().run();
