import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Register', () => {
  test('affiche le formulaire d\'inscription', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/register');
    await expect(page.getByText('Inscription')).toBeVisible();
    await expect(page.getByLabel(/Nom d'utilisateur/)).toBeVisible();
    await expect(page.getByLabel(/Email/)).toBeVisible();
    await expect(page.getByRole('button', { name: /S'inscrire/ })).toBeVisible();
  });

  test('affiche la case politique de confidentialité', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/register');
    await expect(page.getByLabel(/politique de confidentialité/)).toBeVisible();
  });

  test('affiche le lien de connexion', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/register');
    await expect(page.getByText(/Connectez-vous/)).toBeVisible();
  });
});
