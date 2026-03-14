import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const invitationHandlers = [
  http.post(`${BASE}/games/:roomCode/invite/`, async ({ request, params }) => {
    const body = (await request.json()) as Record<string, string>;
    return HttpResponse.json({
      id: 'inv-new-' + Date.now(),
      room_code: params.roomCode,
      game_mode: 'classique',
      game_name: null,
      sender: { id: 1, username: 'alice' },
      recipient: { id: 2, username: body.username },
      status: 'pending',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 300_000).toISOString(),
      is_expired: false,
    });
  }),

  http.get(`${BASE}/games/my-invitations/`, () => {
    const db = getDB();
    return HttpResponse.json(db.invitations);
  }),

  http.post(`${BASE}/games/invitations/:id/accept/`, () => {
    return HttpResponse.json({ room_code: 'ABC123', message: 'Invitation acceptée.' });
  }),

  http.post(`${BASE}/games/invitations/:id/decline/`, () => {
    return HttpResponse.json({ message: 'Invitation refusée.' });
  }),
];
