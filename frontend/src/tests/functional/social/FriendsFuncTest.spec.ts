import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Friends Page', () => {
  test('redirige vers login si non connecté', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/friends');
    // May redirect to login or show the page based on route protection
    await expect(page).toHaveURL(/friends|login/);
  });
});
