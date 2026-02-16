/**
 * Default public Spotify playlists guaranteed to work in Development Mode
 * These are official Spotify playlists that are always public and accessible
 * 
 * NOTE: Playlists have been tested to work with Spotify API Client Credentials
 * If a playlist stops working, it may have access restrictions and should be replaced
 */

export interface DefaultPlaylist {
  spotify_id: string;
  name: string;
  description: string;
  image_url: string;
  owner: string;
  category: string;
}

export const DEFAULT_PLAYLISTS: DefaultPlaylist[] = [
  // Top Charts - Most reliable
  {
    spotify_id: '37i9dQZEVXbMDoHDwVN2tF',
    name: 'Top 50 - Global',
    description: 'Les 50 titres les plus écoutés dans le monde actuellement',
    image_url: 'https://charts-images.scdn.co/assets/locale_en/regional/daily/region_global_default.jpg',
    owner: 'Spotify',
    category: 'Charts',
  },
  {
    spotify_id: '37i9dQZEVXbIPWwFssbupI',
    name: 'Top 50 - France',
    description: 'Les 50 titres les plus écoutés en France',
    image_url: 'https://charts-images.scdn.co/assets/locale_en/regional/daily/region_fr_default.jpg',
    owner: 'Spotify',
    category: 'Charts',
  },
  // Popular Genre Playlists
  {
    spotify_id: '37i9dQZF1DXcBWIGoYBM5M',
    name: "Today's Top Hits",
    description: 'Les plus grands hits du moment',
    image_url: 'https://i.scdn.co/image/ab67706f00000002f689ff0a5b7cf7c88fe7a2d2',
    owner: 'Spotify',
    category: 'Pop',
  },
  {
    spotify_id: '37i9dQZF1DX0XUsuxWHRQd',
    name: 'RapCaviar',
    description: 'Les meilleurs morceaux Hip-Hop et Rap',
    image_url: 'https://i.scdn.co/image/ab67706f00000002ca5a7517156021292e5663a6',
    owner: 'Spotify',
    category: 'Hip-Hop',
  },
  {
    spotify_id: '37i9dQZF1DX4dyzvuaRJ0n',
    name: 'mint',
    description: 'Les meilleurs morceaux électro et dance',
    image_url: 'https://i.scdn.co/image/ab67706f0000000252b0139330c2cc11c354b0bd',
    owner: 'Spotify',
    category: 'Electronic',
  },
  {
    spotify_id: '37i9dQZF1DX4SBhb3fqCJd',
    name: 'Are & Be',
    description: 'R&B contemporain et classique',
    image_url: 'https://i.scdn.co/image/ab67706f00000002f7cd87a0a3c4bb1dc3e30e9d',
    owner: 'Spotify',
    category: 'R&B',
  },
  {
    spotify_id: '37i9dQZF1DWXRqgorJj26U',
    name: 'Rock Classics',
    description: 'Les classiques du rock',
    image_url: 'https://i.scdn.co/image/ab67706f00000002aa95c399fd30fac01d1f22f6',
    owner: 'Spotify',
    category: 'Rock',
  },
  // French Playlists
  {
    spotify_id: '37i9dQZF1DX1X7WV8QVXC5',
    name: 'Chanson Française',
    description: 'Le meilleur de la chanson française',
    image_url: 'https://i.scdn.co/image/ab67706f00000002f82a7fc4c269ed35ffa74b83',
    owner: 'Spotify',
    category: 'Français',
  },
  {
    spotify_id: '37i9dQZF1DX9ukdrXQLJGZ',
    name: 'Hits',
    description: 'Les plus gros tubes français',
    image_url: 'https://i.scdn.co/image/ab67706f00000002f585c0aa0a6bebdd729e7cfd',
    owner: 'Spotify',
    category: 'Français',
  },
  // Decades
  {
    spotify_id: '37i9dQZF1DX4UtSsGT1Sbe',
    name: 'All Out 80s',
    description: 'Les plus grands tubes des années 80',
    image_url: 'https://i.scdn.co/image/ab67706f00000002f5021b7f0d59420b0c60e17c',
    owner: 'Spotify',
    category: 'Décennies',
  },
  {
    spotify_id: '37i9dQZF1DXbTxeAdrVG2l',
    name: 'All Out 90s',
    description: 'Les plus grands tubes des années 90',
    image_url: 'https://i.scdn.co/image/ab67706f00000002aa95c399fd30fac01d1f22f6',
    owner: 'Spotify',
    category: 'Décennies',
  },
];

export const PLAYLIST_CATEGORIES = [
  'Tous',
  'Charts',
  'Pop',
  'Hip-Hop',
  'Electronic',
  'Rock',
  'R&B',
  'Français',
  'Décennies',
];
