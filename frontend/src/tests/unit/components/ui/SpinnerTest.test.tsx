import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner, LoadingState } from '@/components/ui/Spinner';
import PageLoader from '@/components/ui/PageLoader';

class SpinnerTest {
  run() {
    describe('Spinner', () => {
      this.testRoleStatus();
      this.testSizes();
    });

    describe('LoadingState', () => {
      this.testMessage();
      this.testDefaultMessage();
    });

    describe('PageLoader', () => {
      this.testDefaultPageLoader();
      this.testCustomMessage();
    });
  }

  private testRoleStatus() {
    it('a le rôle status', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  }

  private testSizes() {
    it.each(['sm', 'md', 'lg'] as const)('size %s — rend sans erreur', (size) => {
      render(<Spinner size={size} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  }

  private testMessage() {
    it('affiche le message', () => {
      render(<LoadingState message="Patience..." />);
      expect(screen.getByText('Patience...')).toBeInTheDocument();
    });
  }

  private testDefaultMessage() {
    it('affiche "Chargement..." par défaut', () => {
      render(<LoadingState />);
      expect(screen.getByText('Chargement...')).toBeInTheDocument();
    });
  }

  private testDefaultPageLoader() {
    it('affiche "Chargement..." par défaut', () => {
      render(<PageLoader />);
      expect(screen.getByText('Chargement...')).toBeInTheDocument();
    });
  }

  private testCustomMessage() {
    it('affiche un message custom', () => {
      render(<PageLoader message="En cours..." />);
      expect(screen.getByText('En cours...')).toBeInTheDocument();
    });
  }
}

new SpinnerTest().run();
