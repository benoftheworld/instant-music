/**
 * Base de données factice en mémoire pour les handlers MSW.
 *
 * Chaque table est une Map<string, entity>.
 * Les handlers MSW lisent / écrivent ici au lieu d'appeler un vrai backend.
 */
import type {
  User,
  Game,
  GamePlayer,
  GameHistory,
  LeaderboardEntry,
  TeamLeaderboardEntry,
  Achievement,
  UserAchievement,
  Friend,
  Friendship,
  GameInvitation,
  Team,
  ShopItem,
  UserInventoryEntry,
  GameBonus,
  ShopSummary,
  UserDetailedStats,
  UserPublicProfile,
  YouTubePlaylist,
  YouTubeTrack,
  KaraokeSong,
} from '@/types';
import type { SiteStatus, LegalPageData } from '@/services/adminService';
import type { LeaderboardResponse, TeamLeaderboardResponse } from '@/services/statsService';

export interface MockDB {
  users: Map<number, User>;
  games: Map<string, Game>;
  gamePlayers: Map<string, GamePlayer[]>;
  gameHistory: GameHistory[];
  leaderboard: LeaderboardEntry[];
  teamLeaderboard: TeamLeaderboardEntry[];
  achievements: Achievement[];
  userAchievements: UserAchievement[];
  friends: Friend[];
  friendships: Friendship[];
  invitations: GameInvitation[];
  teams: Team[];
  shopItems: ShopItem[];
  inventory: UserInventoryEntry[];
  gameBonuses: GameBonus[];
  shopSummary: ShopSummary;
  userStats: UserDetailedStats;
  publicProfiles: Map<string, UserPublicProfile>;
  playlists: YouTubePlaylist[];
  tracks: Map<string, YouTubeTrack[]>;
  karaokeSongs: KaraokeSong[];
  siteStatus: SiteStatus;
  legalPages: Map<string, LegalPageData>;
  leaderboardResponse: LeaderboardResponse;
  teamLeaderboardResponse: TeamLeaderboardResponse;
  // Auth state
  currentUser: User | null;
  accessToken: string;
  refreshToken: string;
}

function createEmptyDB(): MockDB {
  return {
    users: new Map(),
    games: new Map(),
    gamePlayers: new Map(),
    gameHistory: [],
    leaderboard: [],
    teamLeaderboard: [],
    achievements: [],
    userAchievements: [],
    friends: [],
    friendships: [],
    invitations: [],
    teams: [],
    shopItems: [],
    inventory: [],
    gameBonuses: [],
    shopSummary: { total_coins_available: 1000, user_balance: 500, items_count: 5 },
    userStats: {
      total_games_played: 10,
      total_wins: 5,
      total_points: 1500,
      win_rate: 50,
      avg_score_per_game: 150,
      best_score: 300,
      total_correct_answers: 40,
      total_answers: 80,
      accuracy: 50,
      avg_response_time: 5.2,
      achievements_unlocked: 3,
      achievements_total: 10,
      recent_games: [],
    },
    publicProfiles: new Map(),
    playlists: [],
    tracks: new Map(),
    karaokeSongs: [],
    siteStatus: {
      maintenance: false,
      maintenance_title: '',
      maintenance_message: '',
      banner: { enabled: false, message: '', color: 'info', dismissible: true },
    },
    legalPages: new Map(),
    leaderboardResponse: { results: [], count: 0, page: 1, page_size: 50 },
    teamLeaderboardResponse: { results: [], count: 0, page: 1, page_size: 50 },
    currentUser: null,
    accessToken: 'mock-access-token',
    refreshToken: 'mock-refresh-token',
  };
}

let db: MockDB = createEmptyDB();

export function getDB(): MockDB {
  return db;
}

export function resetDB(): void {
  db = createEmptyDB();
}

export function seedDB(partial: Partial<MockDB>): void {
  Object.assign(db, partial);
}
