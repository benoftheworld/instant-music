import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Page Classement', () => {
  test('affiche le titre classement', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/leaderboard');
    await expect(page.getByText(/classement|leaderboard/i)).toBeVisible();
  });

  test('affiche les onglets joueurs/équipes', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/leaderboard');
    await expect(page.getByRole('tab').first()).toBeVisible();
  });

  test('affiche la liste des joueurs', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/leaderboard');
    await expect(page.getByRole('table').or(page.getByRole('list'))).toBeVisible();
  });

  test('permet de changer de mode de jeu', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/leaderboard');
    const tabs = page.getByRole('tab');
    const count = await tabs.count();
    if (count > 1) {
      await tabs.nth(1).click();
      await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
    }
  });
});
