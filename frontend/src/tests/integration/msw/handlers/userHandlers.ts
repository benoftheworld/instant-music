import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const userHandlers = [
  http.get(`${BASE}/users/me/`, () => {
    const db = getDB();
    if (!db.currentUser) {
      return HttpResponse.json({ detail: 'Non authentifié.' }, { status: 401 });
    }
    return HttpResponse.json(db.currentUser);
  }),

  http.patch(`${BASE}/users/me/`, async ({ request }) => {
    const db = getDB();
    if (!db.currentUser) {
      return HttpResponse.json({ detail: 'Non authentifié.' }, { status: 401 });
    }
    const body = (await request.json()) as Record<string, unknown>;
    Object.assign(db.currentUser, body);
    return HttpResponse.json(db.currentUser);
  }),

  http.post(`${BASE}/users/change_password/`, () => {
    return HttpResponse.json({ detail: 'Mot de passe modifié.' });
  }),

  http.get(`${BASE}/users/exists/`, ({ request }) => {
    const url = new URL(request.url);
    const db = getDB();
    const username = url.searchParams.get('username');
    const email = url.searchParams.get('email');
    if (username) {
      const exists = [...db.users.values()].some((u) => u.username === username);
      return HttpResponse.json({ exists });
    }
    if (email) {
      const exists = [...db.users.values()].some((u) => u.email === email);
      return HttpResponse.json({ exists });
    }
    return HttpResponse.json({ exists: false });
  }),

  http.post(`${BASE}/users/cookie_consent/`, () => {
    return HttpResponse.json({ detail: 'ok' });
  }),

  http.get(`${BASE}/users/search/`, ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const db = getDB();
    const results = [...db.users.values()]
      .filter((u) => u.username.toLowerCase().includes(q.toLowerCase()))
      .map((u) => ({ id: u.id, username: u.username, avatar: u.avatar ?? null, total_points: u.total_points, total_wins: u.total_wins }));
    return HttpResponse.json(results);
  }),
];
