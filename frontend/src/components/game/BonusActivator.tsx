/**
 * BonusActivator — panneau d'activation des bonus en pleine partie.
 *
 * Usage (dans GamePlayPage) :
 *   <BonusActivator roomCode={roomCode} />
 */

import { useState, useEffect, useCallback } from 'react';
import { shopService } from '@/services/shopService';
import { BONUS_META } from '@/constants/bonuses';
import type { BonusType, UserInventoryEntry } from '@/types';

interface Props {
  roomCode: string;
  /** Callback quand un bonus est activé avec succès */
  onBonusActivated?: (bonusType: BonusType, extra: {
    excludedOptions?: string[];
    newDuration?: number;
    stolenPoints?: number;
  }) => void;
}

export default function BonusActivator({ roomCode, onBonusActivated }: Props) {
  const [inventory, setInventory] = useState<UserInventoryEntry[]>([]);
  const [activating, setActivating] = useState<BonusType | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  const loadInventory = useCallback(async () => {
    try {
      const data = await shopService.getInventory();
      setInventory(data.filter((e) => e.quantity > 0 && e.item.item_type === 'bonus'));
    } catch {
      // silencieux
    }
  }, []);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  // Regrouper par type de bonus
  const bonusCountMap = inventory.reduce<Record<string, { entry: UserInventoryEntry; count: number }>>(
    (acc, entry) => {
      if (entry.item.bonus_type) {
        acc[entry.item.bonus_type] = { entry, count: entry.quantity };
      }
      return acc;
    },
    {}
  );

  const availableBonuses = Object.entries(bonusCountMap);

  const handleActivate = async (bonusType: BonusType) => {
    setActivating(bonusType);
    setNotification(null);

    try {
      const result = await shopService.activateBonus(bonusType, roomCode);
      setNotification({ type: 'success', text: `${BONUS_META[bonusType].label} activé !` });
      onBonusActivated?.(bonusType, {
        excludedOptions: result.excluded_options,
        newDuration: result.new_duration,
        stolenPoints: result.stolen_points,
      });
      // Recharger l'inventaire
      await loadInventory();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Impossible d'activer ce bonus.";
      setNotification({ type: 'error', text: detail });
    } finally {
      setActivating(null);
      // Effacer la notification après 3 secondes
      setTimeout(() => setNotification(null), 3000);
    }
  };

  if (availableBonuses.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      {/* Notification */}
      {notification && (
        <div
          className={`text-xs font-semibold px-3 py-2 rounded-lg shadow-lg transition-all ${
            notification.type === 'success'
              ? 'bg-green-700 text-white'
              : 'bg-red-700 text-white'
          }`}
        >
          {notification.text}
        </div>
      )}

      {/* Panneau bonus */}
      <div className="bg-dark-800 border border-primary-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <button
          className="flex items-center justify-between w-full px-4 py-2.5 text-left hover:bg-dark-700 transition-colors"
          onClick={() => setCollapsed((c) => !c)}
        >
          <span className="text-sm font-bold text-primary-300 flex items-center gap-2">
            ⚡ Bonus disponibles
          </span>
          <span className="text-gray-400 text-xs">{collapsed ? '▲' : '▼'}</span>
        </button>

        {/* Liste des bonus */}
        {!collapsed && (
          <div className="px-3 pb-3 flex flex-wrap gap-2 max-w-xs">
            {availableBonuses.map(([bonusType, { count }]) => {
              const meta = BONUS_META[bonusType as BonusType];
              const isActivating = activating === bonusType;

              return (
                <button
                  key={bonusType}
                  title={meta.description}
                  disabled={isActivating}
                  onClick={() => handleActivate(bonusType as BonusType)}
                  className={`relative flex flex-col items-center gap-1 w-16 py-2 px-1 rounded-xl text-white text-xs font-bold shadow transition-all hover:scale-105 active:scale-95 disabled:opacity-60 disabled:cursor-wait ${meta.gradientClass}`}
                >
                  <span className="text-xl leading-none">{isActivating ? '…' : meta.emoji}</span>
                  <span className="text-[10px] leading-none text-center">{meta.shortLabel}</span>
                  {/* Badge quantité */}
                  <span className="absolute -top-1.5 -right-1.5 bg-yellow-400 text-dark text-[10px] font-black rounded-full w-4 h-4 flex items-center justify-center shadow">
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
