import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FormField from '@/components/ui/FormField';

class FormFieldTest {
  run() {
    describe('FormField', () => {
      this.testRendersLabel();
      this.testRendersInput();
      this.testShowsError();
      this.testShowsHint();
      this.testAriaInvalid();
    });
  }

  private testRendersLabel() {
    it('affiche le label', () => {
      render(<FormField label="Email" />);
      expect(screen.getByText('Email')).toBeInTheDocument();
    });
  }

  private testRendersInput() {
    it('rend un input', () => {
      render(<FormField label="Nom" type="text" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  }

  private testShowsError() {
    it('affiche le message d\'erreur', () => {
      render(<FormField label="Email" error="Champ requis" />);
      expect(screen.getByText('Champ requis')).toBeInTheDocument();
    });
  }

  private testShowsHint() {
    it('affiche le hint si pas d\'erreur', () => {
      render(<FormField label="Pseudo" hint="3-20 caractères" />);
      expect(screen.getByText('3-20 caractères')).toBeInTheDocument();
    });
  }

  private testAriaInvalid() {
    it('aria-invalid true si erreur', () => {
      render(<FormField label="Pwd" error="trop court" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
    });
  }
}

new FormFieldTest().run();
