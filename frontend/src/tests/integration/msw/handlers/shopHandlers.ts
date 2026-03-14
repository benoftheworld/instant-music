import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const shopHandlers = [
  http.get(`${BASE}/shop/items/`, () => {
    const db = getDB();
    return HttpResponse.json(db.shopItems);
  }),

  http.get(`${BASE}/shop/items/summary/`, () => {
    const db = getDB();
    return HttpResponse.json(db.shopSummary);
  }),

  http.post(`${BASE}/shop/items/purchase/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const db = getDB();
    const item = db.shopItems.find((i) => i.id === body.item_id);
    if (!item) {
      return HttpResponse.json({ detail: 'Article introuvable.' }, { status: 404 });
    }
    const entry = {
      id: 'purchase-' + Date.now(),
      item,
      quantity: (body.quantity as number) || 1,
      purchased_at: new Date().toISOString(),
    };
    return HttpResponse.json(entry);
  }),

  http.get(`${BASE}/shop/inventory/`, () => {
    const db = getDB();
    return HttpResponse.json(db.inventory);
  }),

  http.post(`${BASE}/shop/inventory/activate/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    return HttpResponse.json({
      id: 'bonus-' + Date.now(),
      bonus_type: body.bonus_type,
      round_number: null,
      activated_at: new Date().toISOString(),
      is_used: false,
      username: 'alice',
    });
  }),

  http.get(`${BASE}/shop/inventory/game/:roomCode/`, () => {
    const db = getDB();
    return HttpResponse.json(db.gameBonuses);
  }),
];
