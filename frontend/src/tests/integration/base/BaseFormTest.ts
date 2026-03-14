/**
 * Classe abstraite pour les tests d'intégration de formulaires.
 *
 * Étend BasePageTest avec des helpers de saisie et soumission.
 */
import { screen } from '@testing-library/react';
import type { UserEvent } from '@testing-library/user-event';
import { BasePageTest } from './BasePageTest';

export abstract class BaseFormTest extends BasePageTest {
  protected async fillField(user: UserEvent, label: string, value: string) {
    const input = screen.getByLabelText(label);
    await user.clear(input);
    await user.type(input, value);
  }

  protected async fillFieldByPlaceholder(user: UserEvent, placeholder: string, value: string) {
    const input = screen.getByPlaceholderText(placeholder);
    await user.clear(input);
    await user.type(input, value);
  }

  protected async submitForm(user: UserEvent, buttonText?: string) {
    const btn = buttonText
      ? screen.getByRole('button', { name: new RegExp(buttonText, 'i') })
      : screen.getByRole('button', { name: /submit|envoyer|valider|connexion|inscription/i });
    await user.click(btn);
  }

  protected async fillAndSubmit(
    user: UserEvent,
    fields: Record<string, string>,
    submitLabel?: string,
  ) {
    for (const [label, value] of Object.entries(fields)) {
      await this.fillField(user, label, value);
    }
    await this.submitForm(user, submitLabel);
  }
}
