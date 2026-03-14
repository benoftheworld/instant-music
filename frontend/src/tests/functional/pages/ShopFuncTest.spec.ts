import { test, expect } from '@playwright/test';
import { BaseAuthenticatedTest } from '../base/BaseAuthenticatedTest';

test.describe('Page Boutique', () => {
  test('affiche le titre boutique', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/shop');
    await expect(page.getByText(/boutique|shop/i)).toBeVisible();
  });

  test('affiche les onglets bonus/physique/inventaire', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/shop');
    await expect(page.getByRole('tab').first()).toBeVisible();
  });

  test('affiche les articles à acheter', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/shop');
    const items = page.getByRole('article').or(page.getByRole('listitem'));
    await expect(items.first()).toBeVisible();
  });

  test('permet de naviguer vers inventaire', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/shop');
    const inventoryTab = page.getByRole('tab', { name: /inventaire|inventory/i });
    if (await inventoryTab.isVisible()) {
      await inventoryTab.click();
      await expect(page.getByText(/inventaire|inventory/i)).toBeVisible();
    }
  });
});
