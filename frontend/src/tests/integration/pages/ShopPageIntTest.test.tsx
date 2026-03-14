import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import ShopPage from '@/pages/ShopPage';

vi.mock('@/hooks/pages/useShopPage', () => ({
  useShopPage: () => ({
    user: { id: 1, username: 'alice', coins_balance: 500 },
    notification: null,
    activeTab: 'bonus',
    setActiveTab: vi.fn(),
    summary: null,
    inventory: [
      { id: 'inv-1', item: { id: 'item-1', name: 'Double Points', bonus_type: 'double_points', description: '', cost: 100, item_type: 'bonus', image: null, is_in_stock: true }, quantity: 2 },
    ],
    loading: false,
    inventoryMap: { 'item-1': 2 } as Record<string, number>,
    handlePurchase: vi.fn(),
    purchasing: null,
    bonusItems: [
      { id: 'item-1', name: 'Double Points', description: 'Double vos points', bonus_type: 'double_points', cost: 100, item_type: 'bonus', image: null, is_in_stock: true },
      { id: 'item-2', name: '50/50', description: 'Élimine 2 choix', bonus_type: 'fifty_fifty', cost: 150, item_type: 'bonus', image: null, is_in_stock: true },
    ],
    physicalItems: [],
  }),
}));

class ShopPageIntTest extends BasePageTest {
  protected getRoute() { return '/shop'; }
  protected getComponent() { return ShopPage; }

  run() {
    describe('ShopPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersShopItems();
      this.testRendersCoinBalance();
    });
  }

  private testRendersShopItems() {
    it('affiche les articles de la boutique', () => {
      this.renderPage();
      expect(screen.getByText('Double Points')).toBeInTheDocument();
      expect(screen.getByText('50/50')).toBeInTheDocument();
    });
  }

  private testRendersCoinBalance() {
    it('affiche le solde', () => {
      this.renderPage();
      expect(screen.getByText('500')).toBeInTheDocument();
    });
  }
}

new ShopPageIntTest().run();
