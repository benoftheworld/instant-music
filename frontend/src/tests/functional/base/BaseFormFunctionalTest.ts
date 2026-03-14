import { type Page } from '@playwright/test';
import { BaseAuthenticatedTest } from './BaseAuthenticatedTest';

/**
 * Classe de base pour les tests fonctionnels de formulaires.
 * Ajoute des helpers de remplissage et soumission.
 */
export class BaseFormFunctionalTest extends BaseAuthenticatedTest {
  constructor(page: Page) {
    super(page);
  }

  async fillForm(fields: Record<string, string>) {
    for (const [label, value] of Object.entries(fields)) {
      await this.fillInput(label, value);
    }
  }

  async submitForm(buttonText: string) {
    await this.clickButton(buttonText);
  }

  async fillAndSubmit(fields: Record<string, string>, buttonText: string) {
    await this.fillForm(fields);
    await this.submitForm(buttonText);
  }
}
