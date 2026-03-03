import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { shopService } from '@/services/shopService';
import type { ShopItem, ShopSummary, UserInventoryEntry } from '@/types';

// ── Icônes des bonus ──────────────────────────────────────────────────────────

const BONUS_META: Record<
  string,
  { emoji: string; label: string; color: string; desc: string }
> = {
  double_points: {
    emoji: '✕2',
    label: 'Points Doublés',
    color: 'from-yellow-500 to-orange-500',
    desc: 'Double vos points sur le prochain round correct',
  },
  max_points: {
    emoji: '⭐',
    label: 'Points Maximum',
    color: 'from-purple-500 to-pink-500',
    desc: 'Obtenez 100 points (score maximum de base) peu importe votre temps de réponse',
  },
  time_bonus: {
    emoji: '⏱️',
    label: 'Temps Bonus',
    color: 'from-blue-500 to-cyan-500',
    desc: '+15 secondes sur le timer du round en cours',
  },
  fifty_fifty: {
    emoji: '½',
    label: '50/50',
    color: 'from-green-500 to-teal-500',
    desc: 'Retire 2 mauvaises réponses de vos choix (mode QCM uniquement)',
  },
  steal: {
    emoji: '🥷',
    label: 'Vol de Points',
    color: 'from-red-500 to-rose-600',
    desc: 'Vole 100 points au joueur en tête',
  },
  shield: {
    emoji: '🛡️',
    label: 'Bouclier',
    color: 'from-gray-400 to-slate-600',
    desc: 'Protège vos points contre un vol',
  },
};

function CoinIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z" />
    </svg>
  );
}

function ShopItemCard({
  item,
  inventoryQuantity,
  userBalance,
  onPurchase,
  purchasing,
}: {
  item: ShopItem;
  inventoryQuantity: number;
  userBalance: number;
  onPurchase: (item: ShopItem) => void;
  purchasing: string | null;
}) {
  const meta = item.bonus_type ? BONUS_META[item.bonus_type] : null;
  const canAfford = userBalance >= item.cost;
  const isPurchasing = purchasing === item.id;

  if (item.item_type === 'physical') {
    const hasCost = item.cost > 0;
    const canAffordPhysical = userBalance >= item.cost;
    const isPurchasingPhysical = purchasing === item.id;
    return (
      <div className={`bg-dark-700 border rounded-xl p-5 flex flex-col gap-3 transition-all ${
        hasCost
          ? canAffordPhysical ? 'border-primary-600 hover:border-primary-400' : 'border-gray-600 opacity-75'
          : 'border-gray-600'
      }`}>
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className="inline-block bg-green-700 text-green-200 text-xs font-bold px-2 py-0.5 rounded-full mb-2">
              🎁 Produit physique
            </span>
            <h3 className="font-bold text-white text-lg">{item.name}</h3>
          </div>
          <span className="text-2xl">📦</span>
        </div>
        <p className="text-gray-300 text-sm flex-1">{item.description}</p>
        {inventoryQuantity > 0 && (
          <div className="text-xs font-semibold text-primary-400">
            Possédé : {inventoryQuantity}x
          </div>
        )}
        <div className="mt-auto">
          {hasCost ? (
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-1.5 text-yellow-400 font-bold text-lg">
                <CoinIcon className="w-5 h-5" />
                <span>{item.cost}</span>
              </div>
              <button
                onClick={() => onPurchase(item)}
                disabled={!canAffordPhysical || isPurchasingPhysical || !item.is_in_stock}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  isPurchasingPhysical
                    ? 'bg-gray-600 text-gray-300 cursor-wait'
                    : !canAffordPhysical
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-primary-600 hover:bg-primary-500 text-white cursor-pointer'
                }`}
              >
                {isPurchasingPhysical ? '…' : !item.is_in_stock ? 'Épuisé' : !canAffordPhysical ? 'Solde insuffisant' : 'Obtenir'}
              </button>
            </div>
          ) : (
            <span className="inline-flex items-center gap-1.5 bg-green-800/60 text-green-200 text-sm font-semibold px-3 py-1.5 rounded-full">
              <span>✓</span> Gratuit
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-dark-700 border rounded-xl p-5 flex flex-col gap-3 transition-all ${
        canAfford
          ? 'border-primary-600 hover:border-primary-400'
          : 'border-gray-600 opacity-75'
      }`}
    >
      {/* Header avec gradient */}
      <div
        className={`w-12 h-12 rounded-xl bg-gradient-to-br ${meta?.color ?? 'from-gray-600 to-gray-700'} flex items-center justify-center text-white text-xl font-black shadow`}
      >
        {meta?.emoji ?? '?'}
      </div>

      <div>
        <h3 className="font-bold text-white text-base">{item.name}</h3>
        <p className="text-gray-400 text-sm mt-1">{item.description}</p>
      </div>

      {/* Inventaire */}
      {inventoryQuantity > 0 && (
        <div className="text-xs font-semibold text-primary-400">
          Possédé : {inventoryQuantity}x
        </div>
      )}

      <div className="mt-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 text-yellow-400 font-bold text-lg">
          <CoinIcon className="w-5 h-5" />
          <span>{item.cost}</span>
        </div>

        <button
          onClick={() => onPurchase(item)}
          disabled={!canAfford || isPurchasing || !item.is_in_stock}
          className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
            isPurchasing
              ? 'bg-gray-600 text-gray-300 cursor-wait'
              : !canAfford
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-500 text-white cursor-pointer'
          }`}
        >
          {isPurchasing ? '…' : !item.is_in_stock ? 'Épuisé' : !canAfford ? 'Solde insuffisant' : 'Acheter'}
        </button>
      </div>
    </div>
  );
}

export default function ShopPage() {
  const { user, updateUser } = useAuthStore();
  const [items, setItems] = useState<ShopItem[]>([]);
  const [summary, setSummary] = useState<ShopSummary | null>(null);
  const [inventory, setInventory] = useState<UserInventoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<'bonus' | 'physical' | 'inventory'>('bonus');

  const inventoryMap = inventory.reduce<Record<string, number>>((acc, entry) => {
    acc[entry.item.id] = entry.quantity;
    return acc;
  }, {});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [itemsData, summaryData, inventoryData] = await Promise.all([
        shopService.getItems(),
        shopService.getSummary(),
        shopService.getInventory(),
      ]);
      setItems(itemsData);
      setSummary(summaryData);
      setInventory(inventoryData);
    } catch {
      setNotification({ type: 'error', text: 'Erreur lors du chargement de la boutique.' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handlePurchase = async (item: ShopItem) => {
    if (!user) return;
    setPurchasing(item.id);
    setNotification(null);

    try {
      await shopService.purchase(item.id, 1);

      // Rafraîchir l'utilisateur et les données de boutique
      const [freshUser, freshSummary, freshInventory] = await Promise.all([
        authService.getCurrentUser(),
        shopService.getSummary(),
        shopService.getInventory(),
      ]);
      updateUser(freshUser);
      setSummary(freshSummary);
      setInventory(freshInventory);

      setNotification({
        type: 'success',
        text: `"${item.name}" ajouté à votre inventaire !`,
      });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Impossible d'effectuer cet achat.";
      setNotification({ type: 'error', text: detail });
    } finally {
      setPurchasing(null);
    }
  };

  const bonusItems = items.filter((i) => i.item_type === 'bonus');
  const physicalItems = items.filter((i) => i.item_type === 'physical');

  const tabClass = (tab: string) =>
    `px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
      activeTab === tab
        ? 'bg-primary-600 text-white'
        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
    }`;

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-5xl mx-auto">

        {/* ── En-tête ── */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-dark-700 mb-1">
            🏪 Boutique
          </h1>
          <p className="text-gray-600 text-sm">
            Dépensez vos pièces pour acheter des bonus à activer en partie, ou
            découvrez les produits physiques disponibles.
          </p>
        </div>

        {/* ── Solde ── */}
        <div className="bg-dark-700 border border-primary-700 rounded-2xl p-5 mb-8 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <CoinIcon className="w-8 h-8 text-yellow-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Votre solde</p>
              <p className="text-3xl font-extrabold text-yellow-400">
                {user?.coins_balance ?? 0}
                <span className="text-base font-normal text-gray-400 ml-1">pièces</span>
              </p>
            </div>
          </div>

          {summary && (
            <div className="text-sm text-gray-400 bg-dark-600 rounded-xl px-4 py-3">
              <p>
                <span className="font-semibold text-white">{summary.total_coins_available}</span> pièces disponibles au total
              </p>
              <p className="text-xs mt-0.5">
                En débloquant tous les achievements
              </p>
            </div>
          )}
        </div>

        {/* ── Notification ── */}
        {notification && (
          <div
            className={`mb-6 px-4 py-3 rounded-xl text-sm font-medium border ${
              notification.type === 'success'
                ? 'bg-green-900/40 border-green-600 text-green-300'
                : 'bg-red-900/40 border-red-600 text-red-300'
            }`}
          >
            {notification.type === 'success' ? '✓ ' : '✕ '}
            {notification.text}
          </div>
        )}

        {/* ── Onglets ── */}
        <div className="flex gap-2 mb-6">
          <button className={tabClass('bonus')} onClick={() => setActiveTab('bonus')}>
            ⚡ Bonus de jeu ({bonusItems.length})
          </button>
          <button className={tabClass('physical')} onClick={() => setActiveTab('physical')}>
            🎁 Produits physiques ({physicalItems.length})
          </button>
          <button className={tabClass('inventory')} onClick={() => setActiveTab('inventory')}>
            🎒 Mon inventaire ({inventory.filter((e) => e.quantity > 0).length})
          </button>
        </div>

        {loading ? (
          <div className="text-center text-gray-400 py-20">Chargement…</div>
        ) : (
          <>
            {/* ── Bonus de jeu ── */}
            {activeTab === 'bonus' && (
              <div>
                <p className="text-gray-400 text-sm mb-5">
                  Activez vos bonus à tout moment pendant une partie pour prendre
                  l'avantage sur vos adversaires.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {bonusItems.map((item) => (
                    <ShopItemCard
                      key={item.id}
                      item={item}
                      inventoryQuantity={inventoryMap[item.id] ?? 0}
                      userBalance={user?.coins_balance ?? 0}
                      onPurchase={handlePurchase}
                      purchasing={purchasing}
                    />
                  ))}
                  {bonusItems.length === 0 && (
                    <p className="col-span-3 text-gray-500 text-center py-10">
                      Aucun bonus disponible.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ── Produits physiques ── */}
            {activeTab === 'physical' && (
              <div>
                <div className="bg-green-900/20 border border-green-700 rounded-xl px-5 py-4 mb-6 text-sm">
                  <strong>ℹ️ Comment obtenir ces produits ?</strong>
                  <br />
                  Ces produits sont des articles physiques. Certains sont <strong>gratuits</strong>, d'autres nécessitent
                  un <strong>coût en pièces</strong> — gagnées grâce à vos succès et performances en jeu.
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {physicalItems.map((item) => (
                    <ShopItemCard
                      key={item.id}
                      item={item}
                      inventoryQuantity={inventoryMap[item.id] ?? 0}
                      userBalance={user?.coins_balance ?? 0}
                      onPurchase={item.cost > 0 ? handlePurchase : () => {}}
                      purchasing={item.cost > 0 ? purchasing : null}
                    />
                  ))}
                  {physicalItems.length === 0 && (
                    <p className="col-span-3 text-gray-500 text-center py-10">
                      Aucun produit disponible pour l'instant.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ── Inventaire ── */}
            {activeTab === 'inventory' && (
              <div>
                <p className="text-gray-400 text-sm mb-5">
                  Vos bonus achetés. Activez-les en pleine partie pour maximiser
                  votre score.
                </p>
                {inventory.filter((e) => e.quantity > 0).length === 0 ? (
                  <div className="text-center text-gray-500 py-14">
                    <p className="text-4xl mb-3">🎒</p>
                    <p>Votre inventaire est vide.</p>
                    <p className="text-sm mt-1">Achetez des bonus dans l'onglet "Bonus de jeu".</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {inventory
                      .filter((e) => e.quantity > 0)
                      .map((entry) => {
                        const meta = entry.item.bonus_type
                          ? BONUS_META[entry.item.bonus_type]
                          : null;
                        return (
                          <div
                            key={entry.id}
                            className="bg-dark-700 border border-primary-700 rounded-xl p-5 flex flex-col gap-3"
                          >
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${meta?.color ?? 'from-gray-600 to-gray-700'} flex items-center justify-center text-white text-xl font-black shadow`}
                              >
                                {meta?.emoji ?? '?'}
                              </div>
                              <div>
                                <h3 className="font-bold text-white text-base">
                                  {entry.item.name}
                                </h3>
                                <p className="text-primary-400 text-sm font-semibold">
                                  {entry.quantity}x disponible{entry.quantity > 1 ? 's' : ''}
                                </p>
                              </div>
                            </div>
                            <p className="text-gray-400 text-sm">
                              {entry.item.description}
                            </p>
                            {entry.item.item_type === 'bonus' && (
                              <p className="text-xs text-gray-500">
                                Activable en partie via le panneau bonus ⚡
                              </p>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
