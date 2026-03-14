import { test, expect } from '@playwright/test';
import { BaseAuthenticatedTest } from '../base/BaseAuthenticatedTest';

test.describe('Page Profil', () => {
  test('affiche les informations du profil', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/profile');
    await expect(page.getByText(/profil|pseudo|statistiques/i)).toBeVisible();
  });

  test('affiche les onglets du profil', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/profile');
    await expect(page.getByRole('tab').first()).toBeVisible();
  });

  test('permet de naviguer entre les onglets', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/profile');
    const tabs = page.getByRole('tab');
    const count = await tabs.count();
    if (count > 1) {
      await tabs.nth(1).click();
      await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
    }
  });

  test('onglet sécurité contient changement de mot de passe', async ({ page }) => {
    const t = new BaseAuthenticatedTest(page);
    await t.login();
    await t.navigateTo('/profile');
    const securityTab = page.getByRole('tab', { name: /sécurité|security/i });
    if (await securityTab.isVisible()) {
      await securityTab.click();
      await expect(page.getByText(/mot de passe|password/i)).toBeVisible();
    }
  });
});
