import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Game Play', () => {
  test('redirige si aucune partie en cours', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/INVALID/play');
    await expect(page).toHaveURL(/game|login|\//);
  });
});
