/**
 * Default YouTube playlists for easy selection
 * Public playlists from popular YouTube music channels
 */

export interface DefaultPlaylist {
  youtube_id: string;
  name: string;
  description: string;
  image_url: string;
  owner: string;
  category: string;
}

export const DEFAULT_PLAYLISTS: DefaultPlaylist[] = [
  // Top Charts / Hits
  {
    youtube_id: 'PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU',
    name: 'Top 100 Songs 2024',
    description: 'Les 100 chansons les plus populaires de 2024',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Charts',
  },
  {
    youtube_id: 'PLgzTt0k8mXzEk586SfMrcTeFdnlPceGGa',
    name: 'Top Pop Hits',
    description: 'Les meilleurs hits pop du moment',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Pop',
  },
  // Hip-Hop / Rap
  {
    youtube_id: 'PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI',
    name: 'Hip Hop Hits',
    description: 'Les meilleurs morceaux Hip-Hop et Rap',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Hip-Hop',
  },
  // Electronic / Dance
  {
    youtube_id: 'PLRqMlBMLVVWERzuOp93OxqhLWFEDW4yA3',
    name: 'Electronic Dance Music',
    description: 'Les meilleurs morceaux électro et dance',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Electronic',
  },
  // Rock
  {
    youtube_id: 'PLhQCJTkrHOwSX8LUnIMgaTq3chP1tiTut',
    name: 'Rock Classics',
    description: 'Les classiques du rock',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Rock',
  },
  // R&B
  {
    youtube_id: 'PLWNXn_iQ2yrKzFTWXxjkFjg0B9oKYMOBi',
    name: 'R&B Essentials',
    description: 'R&B contemporain et classique',
    image_url: '',
    owner: 'YouTube Music',
    category: 'R&B',
  },
  // French Music
  {
    youtube_id: 'PLw2BeOjATqrtH_e7YYUBqZT47HDQWP9JD',
    name: 'Chanson Française',
    description: 'Le meilleur de la chanson française',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Français',
  },
  {
    youtube_id: 'PLyORnIW1xT6waC0PNjAMj5Oud_oLbHaWP',
    name: 'Rap Français',
    description: 'Les meilleurs morceaux de rap français',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Français',
  },
  // Decades
  {
    youtube_id: 'PLGBuKfnErZlCkRXnszjhFENXFBGPBhBRl',
    name: 'Hits des années 80',
    description: 'Les plus grands tubes des années 80',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Décennies',
  },
  {
    youtube_id: 'PLHmPFY7lXhKQxzBbR9sqHj_PvEuIhvVXN',
    name: 'Hits des années 90',
    description: 'Les plus grands tubes des années 90',
    image_url: '',
    owner: 'YouTube Music',
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
