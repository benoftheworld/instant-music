import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Page Mentions légales', () => {
  test('affiche le titre', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/legal');
    await expect(page.getByText(/mention|légal|legal/i)).toBeVisible();
  });

  test('affiche le contenu légal', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/legal');
    await expect(page.locator('main, article, [role="main"]').first()).toBeVisible();
  });
});
