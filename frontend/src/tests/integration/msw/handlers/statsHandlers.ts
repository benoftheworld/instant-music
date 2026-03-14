import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const statsHandlers = [
  http.get(`${BASE}/stats/me/`, () => {
    const db = getDB();
    return HttpResponse.json(db.userStats);
  }),

  http.get(`${BASE}/stats/leaderboard/`, () => {
    const db = getDB();
    return HttpResponse.json(db.leaderboardResponse);
  }),

  http.get(`${BASE}/stats/leaderboard/teams/`, () => {
    const db = getDB();
    return HttpResponse.json(db.teamLeaderboardResponse);
  }),

  http.get(`${BASE}/stats/leaderboard/:mode/`, () => {
    const db = getDB();
    return HttpResponse.json(db.leaderboardResponse);
  }),

  http.get(`${BASE}/stats/my-rank/`, () => {
    return HttpResponse.json({
      general_rank: 1,
      total_players: 100,
      mode_ranks: {},
    });
  }),

  http.get(`${BASE}/stats/user/:userId/`, ({ params }) => {
    const db = getDB();
    const profile = db.publicProfiles.get(params.userId as string);
    if (!profile) {
      return HttpResponse.json({ detail: 'Utilisateur introuvable.' }, { status: 404 });
    }
    return HttpResponse.json(profile);
  }),
];
