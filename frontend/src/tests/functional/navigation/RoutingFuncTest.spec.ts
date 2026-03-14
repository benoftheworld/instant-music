import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Routing', () => {
  test('page d\'accueil se charge', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/');
    await expect(page.getByText(/InstantMusic/)).toBeVisible();
  });

  test('page 404 pour une route inconnue', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/cette-page-nexiste-pas');
    // Should show 404 or redirect to home
    await expect(page.getByText(/404|Page non trouvée|InstantMusic/)).toBeVisible();
  });

  test('page de login se charge', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/login');
    await expect(page.getByText('Connexion')).toBeVisible();
  });

  test('page d\'inscription se charge', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/register');
    await expect(page.getByText('Inscription')).toBeVisible();
  });

  test('page privacy se charge', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/privacy');
    await expect(page).toHaveURL(/privacy/);
  });

  test('page legal se charge', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/legal');
    await expect(page).toHaveURL(/legal/);
  });
});
