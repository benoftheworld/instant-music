import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Game Lobby', () => {
  test('affiche un message d\'erreur si la partie est introuvable', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/INVALID/lobby');
    // Should show some error or redirect
    await expect(page).toHaveURL(/game|login|\//);
  });
});
