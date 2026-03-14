import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Reset Password', () => {
  test('affiche le formulaire de nouveau mot de passe', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/reset-password/abc123/token456');
    await expect(page.getByText('Nouveau mot de passe')).toBeVisible();
    await expect(page.getByLabel(/Nouveau mot de passe/)).toBeVisible();
    await expect(page.getByLabel(/Confirmer/)).toBeVisible();
  });
});
