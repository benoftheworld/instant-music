import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const achievementHandlers = [
  http.get(`${BASE}/achievements/`, () => {
    const db = getDB();
    return HttpResponse.json(db.achievements);
  }),

  http.get(`${BASE}/achievements/mine/`, () => {
    const db = getDB();
    return HttpResponse.json(db.userAchievements);
  }),

  http.get(`${BASE}/achievements/user/:userId/`, () => {
    const db = getDB();
    return HttpResponse.json(db.userAchievements);
  }),
];
