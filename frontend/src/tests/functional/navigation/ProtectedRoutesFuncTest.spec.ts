import { test, expect } from '@playwright/test';
import { BaseFunctionalTest } from '../base/BaseFunctionalTest';

test.describe('Protected Routes', () => {
  test('redirige vers login pour /profile', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/profile');
    await expect(page).toHaveURL(/login|profile/);
  });

  test('redirige vers login pour /game/create', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/game/create');
    await expect(page).toHaveURL(/login|game/);
  });

  test('redirige vers login pour /friends', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/friends');
    await expect(page).toHaveURL(/login|friends/);
  });

  test('redirige vers login pour /shop', async ({ page }) => {
    const t = new BaseFunctionalTest(page);
    await t.navigateTo('/shop');
    await expect(page).toHaveURL(/login|shop/);
  });
});
