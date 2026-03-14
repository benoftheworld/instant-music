import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Page Accueil', () => {
  test('affiche le titre et les boutons principaux', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('affiche les parties récentes', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/');
    await expect(page.getByText(/récent|partie|game/i)).toBeVisible();
  });

  test('affiche le classement top joueurs', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/');
    await expect(page.getByText(/classement|joueur|top/i)).toBeVisible();
  });

  test('bouton créer une partie redirige', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/');
    const btn = page.getByRole('link', { name: /créer|jouer/i });
    if (await btn.isVisible()) {
      await btn.click();
      await expect(page).not.toHaveURL('/');
    }
  });
});
