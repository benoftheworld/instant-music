import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MaintenancePage from '@/components/layout/MaintenancePage';

class MaintenancePageTest {
  run() {
    describe('MaintenancePage', () => {
      this.testRendersTitle();
      this.testRendersMessage();
      this.testDefaultTexts();
    });
  }

  private testRendersTitle() {
    it('affiche le titre fourni', () => {
      render(<MaintenancePage title="En pause" message="Retour bientôt" />);
      expect(screen.getByText('En pause')).toBeInTheDocument();
    });
  }

  private testRendersMessage() {
    it('affiche le message fourni', () => {
      render(<MaintenancePage title="T" message="Custom msg" />);
      expect(screen.getByText('Custom msg')).toBeInTheDocument();
    });
  }

  private testDefaultTexts() {
    it('affiche les textes par défaut si vides', () => {
      render(<MaintenancePage title="" message="" />);
      expect(screen.getByText('Maintenance en cours')).toBeInTheDocument();
    });
  }
}

new MaintenancePageTest().run();
