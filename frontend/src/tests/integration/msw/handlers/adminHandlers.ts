import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const adminHandlers = [
  http.get(`${BASE}/administration/status/`, () => {
    const db = getDB();
    return HttpResponse.json(db.siteStatus);
  }),

  http.get(`${BASE}/administration/legal/:type/`, ({ params }) => {
    const db = getDB();
    const page = db.legalPages.get(params.type as string);
    if (!page) {
      return HttpResponse.json({
        title: params.type === 'legal' ? 'Mentions légales' : 'Politique de confidentialité',
        content: '<p>Contenu légal de test.</p>',
        updated_at: new Date().toISOString(),
      });
    }
    return HttpResponse.json(page);
  }),
];
