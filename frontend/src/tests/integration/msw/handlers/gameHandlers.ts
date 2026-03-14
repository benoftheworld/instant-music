import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const gameHandlers = [
  http.get(`${BASE}/games/history/`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page') || 1);
    const pageSize = Number(url.searchParams.get('page_size') || 20);
    const mode = url.searchParams.get('mode');
    const db = getDB();
    let items = db.gameHistory;
    if (mode) items = items.filter((g) => g.mode === mode);
    const start = (page - 1) * pageSize;
    return HttpResponse.json({ results: items.slice(start, start + pageSize), count: items.length });
  }),

  http.get(`${BASE}/games/leaderboard/`, ({ request }) => {
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get('limit') || 10);
    const db = getDB();
    return HttpResponse.json(db.leaderboard.slice(0, limit));
  }),

  http.post(`${BASE}/games/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const db = getDB();
    const roomCode = 'NEW' + Math.random().toString(36).slice(2, 6).toUpperCase();
    const game = {
      id: roomCode,
      room_code: roomCode,
      host: db.currentUser?.id ?? 1,
      host_username: db.currentUser?.username ?? 'host',
      status: 'waiting' as const,
      players: [],
      player_count: 0,
      created_at: new Date().toISOString(),
      ...body,
    };
    db.games.set(roomCode, game as any);
    return HttpResponse.json(game, { status: 201 });
  }),

  http.get(`${BASE}/games/public/`, () => {
    const db = getDB();
    const publicGames = [...db.games.values()].filter((g) => g.is_public);
    return HttpResponse.json({ results: publicGames });
  }),

  http.get(`${BASE}/games/:roomCode/`, ({ params }) => {
    const db = getDB();
    const game = db.games.get(params.roomCode as string);
    if (!game) return HttpResponse.json({ detail: 'Partie introuvable.' }, { status: 404 });
    return HttpResponse.json(game);
  }),

  http.patch(`${BASE}/games/:roomCode/`, async ({ params, request }) => {
    const db = getDB();
    const game = db.games.get(params.roomCode as string);
    if (!game) return HttpResponse.json({ detail: 'Partie introuvable.' }, { status: 404 });
    const body = (await request.json()) as Record<string, unknown>;
    Object.assign(game, body);
    return HttpResponse.json(game);
  }),

  http.post(`${BASE}/games/:roomCode/join/`, ({ params }) => {
    const db = getDB();
    const game = db.games.get(params.roomCode as string);
    if (!game) return HttpResponse.json({ detail: 'Partie introuvable.' }, { status: 404 });
    const player = {
      id: db.currentUser?.id ?? 99,
      username: db.currentUser?.username ?? 'guest',
      score: 0,
    };
    return HttpResponse.json(player);
  }),

  http.post(`${BASE}/games/:roomCode/leave/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${BASE}/games/:roomCode/start/`, ({ params }) => {
    const db = getDB();
    const game = db.games.get(params.roomCode as string);
    if (!game) return HttpResponse.json({ detail: 'Partie introuvable.' }, { status: 404 });
    game.status = 'in_progress';
    return HttpResponse.json(game);
  }),

  http.get(`${BASE}/games/:roomCode/current-round/`, () => {
    return HttpResponse.json({ current_round: null, message: 'En attente du prochain round.' });
  }),

  http.post(`${BASE}/games/:roomCode/answer/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      id: 1,
      round: 1,
      player: 1,
      answer: body.answer,
      is_correct: true,
      points_earned: 100,
      response_time: body.response_time,
      answered_at: new Date().toISOString(),
    });
  }),

  http.post(`${BASE}/games/:roomCode/end-round/`, () => {
    return HttpResponse.json({ message: 'Round terminé.', correct_answer: 'Artist Name' });
  }),

  http.post(`${BASE}/games/:roomCode/next-round/`, () => {
    return HttpResponse.json({ message: 'Prochain round lancé.' });
  }),

  http.get(`${BASE}/games/:roomCode/results/`, ({ params }) => {
    const db = getDB();
    const game = db.games.get(params.roomCode as string);
    return HttpResponse.json({
      game: { ...(game ?? {}), mode_display: 'Classique', answer_mode_display: 'QCM', guess_target_display: 'Artiste' },
      rankings: db.gamePlayers.get(params.roomCode as string) ?? [],
      rounds: [],
    });
  }),

  http.get(`${BASE}/games/:roomCode/results/pdf/`, () => {
    return new HttpResponse(new Blob(['pdf-content']), {
      headers: { 'Content-Type': 'application/pdf' },
    });
  }),

  http.get(`${BASE}/games/karaoke-songs/`, () => {
    const db = getDB();
    return HttpResponse.json(db.karaokeSongs);
  }),

  http.get(`${BASE}/games/my-invitations/`, () => {
    const db = getDB();
    return HttpResponse.json(db.invitations);
  }),

  http.post(`${BASE}/games/:roomCode/invite/`, async ({ request, params }) => {
    const body = (await request.json()) as Record<string, string>;
    return HttpResponse.json({
      id: 'inv-new',
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

  http.post(`${BASE}/games/invitations/:id/accept/`, () => {
    return HttpResponse.json({ room_code: 'ABC123', message: 'Invitation acceptée.' });
  }),

  http.post(`${BASE}/games/invitations/:id/decline/`, () => {
    return HttpResponse.json({ message: 'Invitation refusée.' });
  }),
];
