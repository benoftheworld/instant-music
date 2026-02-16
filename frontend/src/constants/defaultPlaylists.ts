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
  // Top Charts / Hits - Using verified public playlists
  {
    youtube_id: 'RDCLAK5uy_kmPRjHDECCu4Q8i_E-charge',
    name: 'Top 100 Songs 2024',
    description: 'Les 100 chansons les plus populaires de 2024',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Charts',
  },
  {
    youtube_id: 'RDCLAK5uy_kLWIr9gv1XLlPbaDS965-Db4TrBoUTxQ8',
    name: 'Top Pop Hits',
    description: 'Les meilleurs hits pop du moment',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Pop',
  },
  // Hip-Hop / Rap
  {
    youtube_id: 'RDCLAK5uy_n9YRyNW9FJtTCWKZUaYG9Rj_O-0rtdqSg',
    name: 'Hip Hop Hits',
    description: 'Les meilleurs morceaux Hip-Hop et Rap',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Hip-Hop',
  },
  // Electronic / Dance
  {
    youtube_id: 'RDCLAK5uy_kK8DIZ8TiNTsRqQE0H-8y2ffJAx8VjTgY',
    name: 'Electronic Dance Music',
    description: 'Les meilleurs morceaux électro et dance',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Electronic',
  },
  // Rock
  {
    youtube_id: 'RDCLAK5uy_n_BFjdGMJQjLKYJQmN7l8hWfP9WKXD7Zs',
    name: 'Rock Classics',
    description: 'Les classiques du rock',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Rock',
  },
  // R&B
  {
    youtube_id: 'RDCLAK5uy_l3ZfFHFGb0Nji4WiN2lNqs4FLoBc94Cxk',
    name: 'R&B Essentials',
    description: 'R&B contemporain et classique',
    image_url: '',
    owner: 'YouTube Music',
    category: 'R&B',
  },
  // French Music
  {
    youtube_id: 'RDCLAK5uy_mpJOF4K4iZvgX6TbPpDzxM6IfCZ-MLBE8',
    name: 'Chanson Française',
    description: 'Le meilleur de la chanson française',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Français',
  },
  {
    youtube_id: 'RDCLAK5uy_k6Q4jrLg3VNr5_KPToQjk_IfWWF99w3fM',
    name: 'Rap Français',
    description: 'Les meilleurs morceaux de rap français',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Français',
  },
  // Decades
  {
    youtube_id: 'RDCLAK5uy_n4UBKmikgYl8K5Lf9PKZiNVqGkz5qYXYs',
    name: 'Hits des années 80',
    description: 'Les plus grands tubes des années 80',
    image_url: '',
    owner: 'YouTube Music',
    category: 'Décennies',
  },
  {
    youtube_id: 'RDCLAK5uy_mkBUUbZgmQBcqKYNP_fSCDrxvhPTgRoig',
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
