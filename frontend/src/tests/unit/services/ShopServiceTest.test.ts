import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { shopService } from '@/services/shopService';
import { api } from '@/services/api';
import { createShopItem, createUserInventoryEntry, createGameBonus } from '@/tests/shared/factories';

class ShopServiceTest extends BaseServiceTest {
  protected name = 'shopService';

  run() {
    describe('shopService', () => {
      this.setup(api);

      this.testGetItemsArray();
      this.testGetItemsPaginated();
      this.testGetSummary();
      this.testPurchase();
      this.testGetInventory();
      this.testActivateBonus();
      this.testGetGameBonuses();
      this.testPurchaseError();
    });
  }

  private testGetItemsArray() {
    it('getItems — format array', async () => {
      const items = [createShopItem()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: items });
      const result = await shopService.getItems();
      expect(result).toEqual(items);
    });
  }

  private testGetItemsPaginated() {
    it('getItems — format paginé', async () => {
      const items = [createShopItem()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { results: items, count: 1 } });
      const result = await shopService.getItems();
      expect(result).toEqual(items);
    });
  }

  private testGetSummary() {
    it('getSummary — succès', async () => {
      const summary = { total_coins_available: 1000, user_balance: 500, items_count: 5 };
      this.mockGet('/shop/items/summary/', summary);
      const result = await shopService.getSummary();
      expect(result.user_balance).toBe(500);
    });
  }

  private testPurchase() {
    it('purchase — succès', async () => {
      const entry = createUserInventoryEntry();
      this.mockPost('/shop/items/purchase/', entry);
      const result = await shopService.purchase('item-1', 1);
      expect(result).toEqual(entry);
    });
  }

  private testGetInventory() {
    it('getInventory — succès', async () => {
      const items = [createUserInventoryEntry()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: items });
      const result = await shopService.getInventory();
      expect(result).toEqual(items);
    });
  }

  private testActivateBonus() {
    it('activateBonus — succès', async () => {
      const bonus = createGameBonus();
      this.mockPost('/shop/inventory/activate/', bonus);
      const result = await shopService.activateBonus('double_points', 'ABC123');
      expect(result.bonus_type).toBe('double_points');
    });
  }

  private testGetGameBonuses() {
    it('getGameBonuses — succès', async () => {
      const bonuses = [createGameBonus()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: bonuses });
      const result = await shopService.getGameBonuses('ABC123');
      expect(result).toEqual(bonuses);
    });
  }

  private testPurchaseError() {
    it('purchase — erreur 400 (solde insuffisant)', async () => {
      this.mockError('post', 400, { detail: 'Solde insuffisant.' });
      await expect(shopService.purchase('item-1')).rejects.toThrow();
    });
  }
}

new ShopServiceTest().run();
