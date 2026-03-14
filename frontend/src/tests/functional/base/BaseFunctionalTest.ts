import { test as base, type Page } from '@playwright/test';

/**
 * Classe de base pour les tests fonctionnels Playwright.
 * Fournit des helpers de navigation et d'attente.
 */
export class BaseFunctionalTest {
  constructor(protected page: Page) {}

  async navigateTo(path: string) {
    await this.page.goto(path);
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async getTextContent(selector: string): Promise<string | null> {
    return this.page.textContent(selector);
  }

  async clickButton(text: string) {
    await this.page.getByRole('button', { name: text }).click();
  }

  async clickLink(text: string) {
    await this.page.getByRole('link', { name: text }).click();
  }

  async fillInput(label: string, value: string) {
    await this.page.getByLabel(label).fill(value);
  }

  async isVisible(text: string): Promise<boolean> {
    return this.page.getByText(text).isVisible();
  }
}

export { base };
