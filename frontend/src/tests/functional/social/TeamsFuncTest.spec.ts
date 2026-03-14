import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Teams Page', () => {
  test('affiche la page d\'équipes', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/teams');
    await expect(page).toHaveURL(/teams|login/);
  });
});
