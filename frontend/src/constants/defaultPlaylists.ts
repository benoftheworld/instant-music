/**
 * Default Deezer playlists for easy selection
 * Public playlists from Deezer editors and popular curators
 */

export interface DefaultPlaylist {
  youtube_id: string;  // kept for interface compat — actually Deezer playlist ID
  name: string;
  description: string;
  image_url: string;
  owner: string;
  category: string;
}

export const DEFAULT_PLAYLISTS: DefaultPlaylist[] = [
  // Top Charts / Hits
  {
    youtube_id: '1363560485',
    name: 'Deezer Hits',
    description: 'Les plus grands hits du moment',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Charts',
  },
  {
    youtube_id: '53362031',
    name: 'Les titres du moment',
    description: 'Les titres les plus écoutés en ce moment',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Charts',
  },
  // Pop
  {
    youtube_id: '1964085082',
    name: 'Feel Good Pop',
    description: 'Pop feel-good pour tous les moments',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Pop',
  },
  {
    youtube_id: '1282483245',
    name: 'Pop All Stars',
    description: 'Les meilleurs hits pop de tous les temps',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Pop',
  },
  // Hip-Hop / Rap
  {
    youtube_id: '3272614282',
    name: 'Rapstars',
    description: 'Les meilleurs morceaux rap du moment',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Hip-Hop',
  },
  {
    youtube_id: '9563400362',
    name: 'Rapstars 2020',
    description: 'Les hits rap des années 2020',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Hip-Hop',
  },
  // Electronic / Dance
  {
    youtube_id: '1902101402',
    name: 'Electronic Hits',
    description: 'Les meilleurs morceaux électro et dance',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Electronic',
  },
  {
    youtube_id: '3801761042',
    name: 'Electronic Essentials',
    description: 'Les essentiels de la musique électronique',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Electronic',
  },
  // Rock
  {
    youtube_id: '1306931615',
    name: 'Rock Essentials',
    description: 'Les 100 morceaux rock incontournables',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Rock',
  },
  {
    youtube_id: '3126664682',
    name: 'Rock Road Trip',
    description: 'Le meilleur du rock pour la route',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Rock',
  },
  // R&B
  {
    youtube_id: '2467857442',
    name: '90s/00s RnB & Soul',
    description: 'Le meilleur du R&B des années 90 et 2000',
    image_url: '',
    owner: 'Deezer',
    category: 'R&B',
  },
  {
    youtube_id: '7537654182',
    name: 'RNB/Rap US 90s-2000s',
    description: 'RnB et Rap US des années 90 à 2000',
    image_url: '',
    owner: 'Deezer',
    category: 'R&B',
  },
  // French Music
  {
    youtube_id: '700895155',
    name: 'Essentiels chanson française',
    description: 'Les essentiels de la chanson française',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Français',
  },
  {
    youtube_id: '1071669561',
    name: 'Actu Rap FR',
    description: 'Les dernières nouveautés du rap français',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Français',
  },
  // Decades
  {
    youtube_id: '1163842311',
    name: 'En mode 80',
    description: 'Les plus grands tubes des années 80',
    image_url: '',
    owner: 'Deezer Editors',
    category: 'Décennies',
  },
  {
    youtube_id: '1251125011',
    name: 'En mode 90',
    description: 'Les plus grands tubes des années 90',
    image_url: '',
    owner: 'Deezer Editors',
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
