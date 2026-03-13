import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { shopService } from '@/services/shopService';
import { QUERY_KEYS } from '@/constants/queryKeys';
import type { ShopItem, ShopSummary, UserInventoryEntry } from '@/types';

export function useShopPage() {
  const { user, updateUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<'bonus' | 'physical' | 'inventory'>('bonus');

  const { data: items = [], isLoading: itemsLoading } = useQuery<ShopItem[]>({
    queryKey: QUERY_KEYS.shopItems(),
    queryFn: () => shopService.getItems(),
  });

  const { data: summary = null } = useQuery<ShopSummary | null>({
    queryKey: QUERY_KEYS.shopSummary(),
    queryFn: () => shopService.getSummary(),
  });

  const { data: inventory = [], isLoading: inventoryLoading } = useQuery<UserInventoryEntry[]>({
    queryKey: QUERY_KEYS.shopInventory(),
    queryFn: () => shopService.getInventory(),
  });

  const loading = itemsLoading || inventoryLoading;

  const inventoryMap = inventory.reduce<Record<string, number>>((acc, entry) => {
    acc[entry.item.id] = entry.quantity;
    return acc;
  }, {});

  const purchaseMutation = useMutation({
    mutationFn: (item: ShopItem) => shopService.purchase(item.id, 1),
    onMutate: () => setNotification(null),
    onSuccess: async (_data, item) => {
      const freshUser = await authService.getCurrentUser();
      updateUser(freshUser);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.shop() });

      setNotification({
        type: 'success',
        text: `"${item.name}" ajouté à votre inventaire !`,
      });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Impossible d'effectuer cet achat.";
      setNotification({ type: 'error', text: detail });
    },
  });

  const handlePurchase = (item: ShopItem) => {
    if (!user) return;
    purchaseMutation.mutate(item);
  };
  const purchasing = purchaseMutation.isPending ? (purchaseMutation.variables?.id ?? null) : null;

  const bonusItems = items.filter((i) => i.item_type === 'bonus');
  const physicalItems = items.filter((i) => i.item_type === 'physical');

  return {
    user,
    notification,
    setNotification,
    activeTab,
    setActiveTab,
    items,
    summary,
    inventory,
    loading,
    inventoryMap,
    handlePurchase,
    purchasing,
    bonusItems,
    physicalItems,
  };
}
