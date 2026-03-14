import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Page Politique de confidentialité', () => {
  test('affiche le titre', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/privacy');
    await expect(page.getByText(/confidentialité|privacy|données/i)).toBeVisible();
  });

  test('affiche le contenu légal', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/privacy');
    await expect(page.locator('main, article, [role="main"]').first()).toBeVisible();
  });
});
