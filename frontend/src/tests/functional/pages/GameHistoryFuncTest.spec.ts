import { test, expect } from '@playwright/test';
import { BaseAuthenticatedTest } from '../base/BaseAuthenticatedTest';

test.describe('Page Historique des parties', () => {
  test('affiche le titre historique', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/history');
    await expect(page.getByText(/historique|parties|game/i)).toBeVisible();
  });

  test('affiche les filtres de mode', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/history');
    await expect(page.getByRole('tab').or(page.getByRole('combobox')).first()).toBeVisible();
  });

  test('affiche un message si aucune partie', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/history');
    const content = page.getByText(/aucune|no game|vide|empty|partie/i);
    const table = page.getByRole('table');
    await expect(content.or(table)).toBeVisible();
  });
});
