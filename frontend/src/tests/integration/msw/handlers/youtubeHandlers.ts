import { http, HttpResponse } from 'msw';
import { getDB } from '../db';

const BASE = '*/api';

export const youtubeHandlers = [
  http.get(`${BASE}/playlists/search/`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query') || '';
    const db = getDB();
    const results = db.playlists.filter(
      (p) => p.name.toLowerCase().includes(query.toLowerCase()),
    );
    return HttpResponse.json({ playlists: results });
  }),

  http.get(`${BASE}/playlists/youtube-songs/search/`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query') || '';
    const db = getDB();
    const allTracks = [...db.tracks.values()].flat();
    const results = allTracks.filter(
      (t) => t.name.toLowerCase().includes(query.toLowerCase()),
    );
    return HttpResponse.json({ tracks: results });
  }),

  http.get(`${BASE}/playlists/:youtubeId/`, ({ params }) => {
    const db = getDB();
    const playlist = db.playlists.find((p) => p.youtube_id === params.youtubeId);
    if (!playlist) {
      return HttpResponse.json({ detail: 'Playlist introuvable.' }, { status: 404 });
    }
    return HttpResponse.json(playlist);
  }),

  http.get(`${BASE}/playlists/:youtubeId/tracks/`, ({ params }) => {
    const db = getDB();
    const tracks = db.tracks.get(params.youtubeId as string) ?? [];
    return HttpResponse.json(tracks);
  }),
];
