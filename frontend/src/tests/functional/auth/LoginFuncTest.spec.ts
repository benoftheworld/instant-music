import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Login', () => {
  test('affiche le formulaire de connexion', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/login');
    await expect(page.getByText('Connexion')).toBeVisible();
    await expect(page.getByLabel(/Identifiant/)).toBeVisible();
    await expect(page.getByLabel(/Mot de passe/)).toBeVisible();
    await expect(page.getByRole('button', { name: /Se connecter/ })).toBeVisible();
  });

  test('affiche le lien mot de passe oublié', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/login');
    await expect(page.getByText(/Mot de passe oublié/)).toBeVisible();
  });

  test('affiche le lien d\'inscription', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/login');
    await expect(page.getByText(/Inscrivez-vous/)).toBeVisible();
  });
});
