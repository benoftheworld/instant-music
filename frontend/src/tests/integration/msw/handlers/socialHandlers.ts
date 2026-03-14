import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const socialHandlers = [
  // Friends
  http.get(`${BASE}/users/friends/`, () => {
    const db = getDB();
    return HttpResponse.json(db.friends);
  }),

  http.get(`${BASE}/users/friends/pending/`, () => {
    const db = getDB();
    return HttpResponse.json(db.friendships.filter((f) => f.status === 'pending'));
  }),

  http.get(`${BASE}/users/friends/sent/`, () => {
    const db = getDB();
    return HttpResponse.json(db.friendships.filter((f) => f.status === 'pending'));
  }),

  http.post(`${BASE}/users/friends/send_request/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    return HttpResponse.json({
      id: 99,
      from_user: { id: 1, username: 'alice', avatar: null, total_points: 0, total_wins: 0 },
      to_user: { id: 99, username: body.username, avatar: null, total_points: 0, total_wins: 0 },
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }),

  http.post(`${BASE}/users/friends/:id/accept/`, () => {
    return HttpResponse.json({ status: 'accepted' });
  }),

  http.post(`${BASE}/users/friends/:id/reject/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.delete(`${BASE}/users/friends/:id/remove/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Teams
  http.get(`${BASE}/users/teams/`, () => {
    const db = getDB();
    return HttpResponse.json(db.teams);
  }),

  http.get(`${BASE}/users/teams/browse/`, () => {
    const db = getDB();
    return HttpResponse.json(db.teams);
  }),

  http.get(`${BASE}/users/teams/:teamId/`, ({ params }) => {
    const db = getDB();
    const team = db.teams.find((t) => t.id === params.teamId);
    if (!team) return HttpResponse.json({ detail: 'Équipe introuvable.' }, { status: 404 });
    return HttpResponse.json(team);
  }),

  http.post(`${BASE}/users/teams/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    return HttpResponse.json({
      id: 'team-new',
      name: body.name,
      description: body.description || '',
      avatar: null,
      owner: { id: 1, username: 'alice', avatar: null, total_points: 0, total_wins: 0 },
      members_list: [],
      member_count: 1,
      total_games: 0,
      total_wins: 0,
      total_points: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.post(`${BASE}/users/teams/:teamId/join/`, ({ params }) => {
    const db = getDB();
    const team = db.teams.find((t) => t.id === params.teamId);
    return HttpResponse.json(team ?? {});
  }),

  http.post(`${BASE}/users/teams/:teamId/leave/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${BASE}/users/teams/:teamId/invite/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${BASE}/users/teams/:teamId/update_member/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${BASE}/users/teams/:teamId/remove_member/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE}/users/teams/:teamId/requests/`, () => {
    return HttpResponse.json([]);
  }),

  http.post(`${BASE}/users/teams/:teamId/approve/`, () => {
    return HttpResponse.json({ detail: 'Demande approuvée.' });
  }),

  http.post(`${BASE}/users/teams/:teamId/reject/`, () => {
    return HttpResponse.json({ detail: 'Demande rejetée.' });
  }),

  http.patch(`${BASE}/users/teams/:teamId/edit/`, () => {
    return HttpResponse.json({});
  }),

  http.get(`${BASE}/users/teams/my_pending_requests/`, () => {
    return HttpResponse.json([]);
  }),

  http.post(`${BASE}/users/teams/:teamId/dissolve/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),
];
