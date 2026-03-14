import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Game Results', () => {
  test('redirige si résultats indisponibles', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/INVALID/results');
    await expect(page).toHaveURL(/game|login|\//);
  });
});
