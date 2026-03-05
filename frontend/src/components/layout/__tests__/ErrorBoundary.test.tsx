import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '@/components/layout/ErrorBoundary';

function ThrowingComponent() {
  throw new Error('Test error');
}

function WorkingComponent() {
  return <div>Content OK</div>;
}

describe('ErrorBoundary', () => {
  it('affiche les enfants quand il n y a pas d erreur', () => {
    render(
      <ErrorBoundary>
        <WorkingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Content OK')).toBeInTheDocument();
  });

  it('affiche le fallback en cas d erreur', () => {
    // Suppress console.error from React for this test
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(
      screen.getByText(/quelque chose s'est mal passé/i)
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /recharger la page/i })).toBeInTheDocument();

    spy.mockRestore();
  });

  it('affiche un fallback custom si fourni', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary fallback={<div>Custom Fallback</div>}>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom Fallback')).toBeInTheDocument();

    spy.mockRestore();
  });
});
