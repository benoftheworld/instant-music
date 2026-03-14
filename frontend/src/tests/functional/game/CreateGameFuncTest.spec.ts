import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Create Game', () => {
  test('affiche la page de création de partie', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/create');
    await expect(page.getByText(/Mode de jeu|Créer une partie/)).toBeVisible();
  });
});
