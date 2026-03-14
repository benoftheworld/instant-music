import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Join Game', () => {
  test('affiche la page pour rejoindre une partie', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/join');
    await expect(page.getByText(/Rejoindre une partie/)).toBeVisible();
  });
});
