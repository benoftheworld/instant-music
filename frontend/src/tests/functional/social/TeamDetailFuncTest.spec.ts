import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Team Detail', () => {
  test('affiche une page d\'équipe ou redirige', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/teams/1');
    await expect(page).toHaveURL(/teams|login/);
  });
});
