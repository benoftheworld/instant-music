import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '@/components/ui/StatCard';

class StatCardTest {
  run() {
    describe('StatCard', () => {
      this.testRendersAll();
    });
  }

  private testRendersAll() {
    it('affiche icône, valeur et label', () => {
      render(
        <StatCard icon="🏆" label="Victoires" value={42} textColor="text-yellow-600" bgClass="bg-yellow-50" />,
      );
      expect(screen.getByText('🏆')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('Victoires')).toBeInTheDocument();
    });
  }
}

new StatCardTest().run();
