import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EmptyState from '@/components/ui/EmptyState';

class EmptyStateTest {
  run() {
    describe('EmptyState', () => {
      this.testRendersTitle();
      this.testDescription();
      this.testIcon();
      this.testAction();
    });
  }

  private testRendersTitle() {
    it('affiche le titre', () => {
      render(<EmptyState title="Aucun résultat" />);
      expect(screen.getByText('Aucun résultat')).toBeInTheDocument();
    });
  }

  private testDescription() {
    it('affiche la description si fournie', () => {
      render(<EmptyState title="Vide" description="Rien ici" />);
      expect(screen.getByText('Rien ici')).toBeInTheDocument();
    });
  }

  private testIcon() {
    it('affiche l\'icône si fournie', () => {
      render(<EmptyState title="T" icon="🎵" />);
      expect(screen.getByText('🎵')).toBeInTheDocument();
    });
  }

  private testAction() {
    it('affiche l\'action si fournie', () => {
      render(<EmptyState title="T" action={<button>Go</button>} />);
      expect(screen.getByRole('button', { name: 'Go' })).toBeInTheDocument();
    });
  }
}

new EmptyStateTest().run();
