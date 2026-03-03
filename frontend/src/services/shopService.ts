import { api } from './api';
import type {
  GameBonus,
  ShopItem,
  ShopSummary,
  UserInventoryEntry,
} from '@/types';

interface PaginatedResult<T> {
  results: T[];
  count: number;
}

export const shopService = {
  /** Récupérer le catalogue de la boutique */
  async getItems(): Promise<ShopItem[]> {
    const response = await api.get<PaginatedResult<ShopItem> | ShopItem[]>(
      '/shop/items/'
    );
    const data = response.data;
    return Array.isArray(data) ? data : (data as PaginatedResult<ShopItem>).results ?? [];
  },

  /** Résumé boutique : solde utilisateur + total pièces disponibles */
  async getSummary(): Promise<ShopSummary> {
    const response = await api.get<ShopSummary>('/shop/items/summary/');
    return response.data;
  },

  /** Acheter un article */
  async purchase(
    itemId: string,
    quantity = 1
  ): Promise<UserInventoryEntry> {
    const response = await api.post<UserInventoryEntry>('/shop/items/purchase/', {
      item_id: itemId,
      quantity,
    });
    return response.data;
  },

  /** Récupérer l'inventaire de l'utilisateur */
  async getInventory(): Promise<UserInventoryEntry[]> {
    const response = await api.get<UserInventoryEntry[]>('/shop/inventory/');
    return response.data;
  },

  /** Activer un bonus dans une partie */
  async activateBonus(
    bonusType: string,
    roomCode: string
  ): Promise<GameBonus> {
    const response = await api.post<GameBonus>('/shop/inventory/activate/', {
      bonus_type: bonusType,
      room_code: roomCode,
    });
    return response.data;
  },

  /** Récupérer les bonus actifs du joueur pour une partie */
  async getGameBonuses(roomCode: string): Promise<GameBonus[]> {
    const response = await api.get<GameBonus[]>(
      `/shop/inventory/game/${roomCode}/`
    );
    return response.data;
  },
};
