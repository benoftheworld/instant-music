import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Forgot Password', () => {
  test('affiche le formulaire de réinitialisation', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/forgot-password');
    await expect(page.getByText('Mot de passe oublié')).toBeVisible();
    await expect(page.getByLabel(/Adresse email/)).toBeVisible();
    await expect(page.getByRole('button', { name: /Envoyer le lien/ })).toBeVisible();
  });

  test('affiche le lien retour à la connexion', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/forgot-password');
    await expect(page.getByText(/Retour à la connexion/)).toBeVisible();
  });
});
