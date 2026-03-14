import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('@/services/shopService', () => ({
  shopService: {
    getInventory: vi.fn(),
    activateBonus: vi.fn(),
  },
}));

vi.mock('@/constants/bonuses', () => ({
  BONUS_META: {
    fifty_fifty: {
      label: '50/50',
      shortLabel: '50/50',
      emoji: '✂️',
      description: 'Retire 2 mauvaises réponses',
      gradientClass: 'bg-blue-500',
    },
    steal: {
      label: 'Vol',
      shortLabel: 'Vol',
      emoji: '🦊',
      description: 'Voler des points',
      gradientClass: 'bg-red-500',
    },
  },
}));

import BonusActivator from '@/components/game/BonusActivator';
import { shopService } from '@/services/shopService';

class BonusActivatorTest {
  run() {
    describe('BonusActivator', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      this.testHiddenWhenDisabled();
      this.testHiddenWhenEmptyInventory();
      this.testShowsBonuses();
      this.testActivateBonus();
    });
  }

  private testHiddenWhenDisabled() {
    it('ne rend rien si bonusesEnabled est false', () => {
      vi.mocked(shopService.getInventory).mockResolvedValue([]);
      const { container } = render(
        <BonusActivator roomCode="ABC123" bonusesEnabled={false} />,
      );
      expect(container.innerHTML).toBe('');
    });
  }

  private testHiddenWhenEmptyInventory() {
    it('ne rend rien si inventaire vide', async () => {
      vi.mocked(shopService.getInventory).mockResolvedValue([]);
      const { container } = render(
        <BonusActivator roomCode="ABC123" />,
      );
      await waitFor(() => {
        expect(container.querySelector('.fixed')).not.toBeInTheDocument();
      });
    });
  }

  private testShowsBonuses() {
    it('affiche les bonus disponibles', async () => {
      vi.mocked(shopService.getInventory).mockResolvedValue([
        {
          id: 1,
          quantity: 2,
          item: { id: 1, name: '50/50', item_type: 'bonus', bonus_type: 'fifty_fifty', price: 10 },
        },
      ] as any);
      render(<BonusActivator roomCode="ABC123" />);
      await waitFor(() => {
        expect(screen.getByText('⚡ Bonus disponibles')).toBeInTheDocument();
      });
    });
  }

  private testActivateBonus() {
    it('active un bonus au clic', async () => {
      vi.mocked(shopService.getInventory).mockResolvedValue([
        {
          id: 1,
          quantity: 1,
          item: { id: 1, name: '50/50', item_type: 'bonus', bonus_type: 'fifty_fifty', price: 10 },
        },
      ] as any);
      vi.mocked(shopService.activateBonus).mockResolvedValue({
        excluded_options: ['A', 'B'],
      } as any);
      const onBonusActivated = vi.fn();
      render(
        <BonusActivator roomCode="ABC123" onBonusActivated={onBonusActivated} />,
      );
      await waitFor(() => {
        expect(screen.getByText('✂️')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('✂️').closest('button')!);
      await waitFor(() => {
        expect(shopService.activateBonus).toHaveBeenCalledWith('fifty_fifty', 'ABC123');
      });
    });
  }
}

new BonusActivatorTest().run();
