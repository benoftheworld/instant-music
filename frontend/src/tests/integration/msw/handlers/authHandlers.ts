import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const authHandlers = [
  http.post(`${BASE}/auth/login/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    const db = getDB();
    const user = [...db.users.values()].find((u) => u.username === body.username);
    if (!user) {
      return HttpResponse.json({ detail: 'Identifiants invalides.' }, { status: 401 });
    }
    db.currentUser = user;
    return HttpResponse.json({ user, tokens: { access: db.accessToken } });
  }),

  http.post(`${BASE}/auth/register/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    const db = getDB();
    const existing = [...db.users.values()].find(
      (u) => u.username === body.username || u.email === body.email,
    );
    if (existing) {
      return HttpResponse.json({ username: ['Ce nom est déjà pris.'] }, { status: 400 });
    }
    const newUser = {
      id: db.users.size + 1,
      username: body.username,
      email: body.email,
      is_staff: false,
      total_games_played: 0,
      total_wins: 0,
      total_points: 0,
      coins_balance: 0,
      win_rate: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    db.users.set(newUser.id, newUser);
    db.currentUser = newUser;
    return HttpResponse.json({ user: newUser, tokens: { access: db.accessToken } }, { status: 201 });
  }),

  http.post(`${BASE}/auth/logout/`, () => {
    const db = getDB();
    db.currentUser = null;
    return HttpResponse.json({}, { status: 200 });
  }),

  http.post(`${BASE}/auth/token/refresh/`, () => {
    const db = getDB();
    return HttpResponse.json({ access: db.accessToken });
  }),

  http.post(`${BASE}/auth/password/reset/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    if (!body.identifier) {
      return HttpResponse.json({ identifier: ['Ce champ est obligatoire.'] }, { status: 400 });
    }
    return HttpResponse.json({ detail: 'Si ce compte existe, un lien de réinitialisation a été envoyé.' });
  }),

  http.post(`${BASE}/auth/password/reset/confirm/`, () => {
    return HttpResponse.json({ detail: 'Mot de passe réinitialisé avec succès.' });
  }),
];
