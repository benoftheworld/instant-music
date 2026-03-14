import { type Page } from '@playwright/test';
import { BaseFunctionalTest } from './BaseFunctionalTest';

/**
 * Classe de base pour les tests fonctionnels avec authentification.
 * Se connecte automatiquement avant chaque test.
 */
export class BaseAuthenticatedTest extends BaseFunctionalTest {
  constructor(page: Page) {
    super(page);
  }

  async login(username = 'alice', password = 'password123') {
    await this.navigateTo('/login');
    await this.fillInput('Identifiant (email ou pseudonyme)', username);
    await this.fillInput('Mot de passe', password);
    await this.clickButton('Se connecter');
    await this.page.waitForURL('/');
  }
}
