/**
 * Factories de données de test pour InstantMusic.
 * Chaque factory retourne un objet avec des valeurs par défaut valides,
 * surchargeable via le paramètre `overrides`.
 */
import type {
  User,
  Game,
  GamePlayer,
  GameRound,
  GameHistory,
  GameParticipant,
  GameWinner,
  GameInvitation,
  LeaderboardEntry,
  TeamLeaderboardEntry,
  Friend,
  Friendship,
  Team,
  TeamMember,
  Achievement,
  UserAchievement,
  ShopItem,
  UserInventoryEntry,
  ShopSummary,
  UserDetailedStats,
  UserPublicProfile,
  UserMinimal,
  KaraokeSong,
  YouTubePlaylist,
  YouTubeTrack,
  WebSocketMessage,
  CreateGameData,
  AuthResponse,
  LoginCredentials,
  RegisterData,
  GameBonus,
} from '@/types';
import type { PendingFriendRequest, SocialNotification } from '@/store/notificationStore';

let _id = 1;
const nextId = () => _id++;
const nextUuid = () => `uuid-${nextId()}`;

export function resetFactoryIds() {
  _id = 1;
}

// ─── User ──────────────────────────────────────────────────────────────────

export function createUser(overrides: Partial<User> = {}): User {
  const id = overrides.id ?? nextId();
  return {
    id,
    username: `user${id}`,
    email: `user${id}@test.com`,
    is_staff: false,
    total_games_played: 10,
    total_wins: 5,
    total_points: 500,
    coins_balance: 100,
    win_rate: 50.0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-06-01T00:00:00Z',
    ...overrides,
  };
}

export function createUserMinimal(overrides: Partial<UserMinimal> = {}): UserMinimal {
  const id = overrides.id ?? nextId();
  return {
    id,
    username: `user${id}`,
    avatar: null,
    total_points: 500,
    total_wins: 5,
    ...overrides,
  };
}

// ─── Auth ──────────────────────────────────────────────────────────────────

export function createLoginCredentials(overrides: Partial<LoginCredentials> = {}): LoginCredentials {
  return {
    username: 'testuser',
    password: 'Password123!',
    ...overrides,
  };
}

export function createRegisterData(overrides: Partial<RegisterData> = {}): RegisterData {
  return {
    username: 'newuser',
    email: 'newuser@test.com',
    password: 'Password123!',
    password2: 'Password123!',
    accept_privacy_policy: true,
    ...overrides,
  };
}

export function createAuthResponse(overrides: Partial<AuthResponse> = {}): AuthResponse {
  return {
    user: createUser(),
    tokens: { access: 'mock-access-token' },
    ...overrides,
  };
}

// Crée un JWT factice avec un payload encodé en base64
export function createMockJwt(payload: Record<string, unknown> = {}): string {
  const defaultPayload = {
    exp: Math.floor(Date.now() / 1000) + 3600, // expire dans 1h
    iat: Math.floor(Date.now() / 1000),
    user_id: 1,
    ...payload,
  };
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(defaultPayload));
  return `${header}.${body}.fake-signature`;
}

export function createExpiredJwt(): string {
  return createMockJwt({ exp: Math.floor(Date.now() / 1000) - 60 });
}

// ─── Game ──────────────────────────────────────────────────────────────────

export function createGame(overrides: Partial<Game> = {}): Game {
  const roomCode = overrides.room_code ?? `RM${nextId()}`;
  return {
    id: nextUuid(),
    room_code: roomCode,
    host: 1,
    host_username: 'host',
    mode: 'classique',
    status: 'waiting',
    max_players: 10,
    num_rounds: 5,
    is_online: true,
    is_public: true,
    is_party_mode: false,
    bonuses_enabled: true,
    answer_mode: 'mcq',
    guess_target: 'title',
    round_duration: 20,
    timer_start_round: 3,
    score_display_duration: 15,
    lyrics_words_count: 3,
    players: [],
    player_count: 1,
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createGamePlayer(overrides: Partial<GamePlayer> = {}): GamePlayer {
  const id = overrides.id ?? nextId();
  return {
    id,
    username: `player${id}`,
    score: 0,
    is_connected: true,
    ...overrides,
  };
}

export function createGameRound(overrides: Partial<GameRound> = {}): GameRound {
  const id = overrides.id ?? nextId();
  return {
    id,
    round_number: 1,
    track_id: `track-${id}`,
    track_name: 'Test Track',
    artist_name: 'Test Artist',
    preview_url: 'https://example.com/preview.mp3',
    options: ['Option A', 'Option B', 'Option C', 'Option D'],
    question_type: 'classique',
    question_text: 'Quel est le titre de cette chanson ?',
    extra_data: {},
    duration: 20,
    started_at: '2024-01-01T12:00:00Z',
    ...overrides,
  };
}

export function createCreateGameData(overrides: Partial<CreateGameData> = {}): CreateGameData {
  return {
    mode: 'classique',
    max_players: 10,
    num_rounds: 5,
    is_online: true,
    is_public: true,
    answer_mode: 'mcq',
    guess_target: 'title',
    round_duration: 20,
    score_display_duration: 15,
    ...overrides,
  };
}

// ─── Game History ──────────────────────────────────────────────────────────

export function createGameHistory(overrides: Partial<GameHistory> = {}): GameHistory {
  return {
    id: nextUuid(),
    room_code: `RM${nextId()}`,
    host_username: 'host',
    mode: 'classique',
    mode_display: 'Classique',
    answer_mode: 'mcq',
    answer_mode_display: 'QCM',
    guess_target: 'title',
    guess_target_display: 'Titre',
    num_rounds: 5,
    playlist_id: null,
    winner: createGameWinner(),
    winner_score: 500,
    player_count: 4,
    participants: [createGameParticipant()],
    created_at: '2024-01-01T00:00:00Z',
    started_at: '2024-01-01T00:01:00Z',
    finished_at: '2024-01-01T00:10:00Z',
    ...overrides,
  };
}

export function createGameParticipant(overrides: Partial<GameParticipant> = {}): GameParticipant {
  const id = overrides.id ?? nextId();
  return {
    id,
    username: `player${id}`,
    avatar: null,
    score: 100,
    rank: 1,
    ...overrides,
  };
}

export function createGameWinner(overrides: Partial<GameWinner> = {}): GameWinner {
  return {
    id: 1,
    username: 'winner',
    avatar: null,
    ...overrides,
  };
}

// ─── Invitation ────────────────────────────────────────────────────────────

export function createGameInvitation(overrides: Partial<GameInvitation> = {}): GameInvitation {
  return {
    id: nextUuid(),
    room_code: 'ABC123',
    game_mode: 'classique',
    game_name: null,
    sender: { id: 1, username: 'host' },
    recipient: { id: 2, username: 'player' },
    status: 'pending',
    created_at: '2024-01-01T00:00:00Z',
    expires_at: '2024-01-01T01:00:00Z',
    is_expired: false,
    ...overrides,
  };
}

// ─── Leaderboard ───────────────────────────────────────────────────────────

export function createLeaderboardEntry(overrides: Partial<LeaderboardEntry> = {}): LeaderboardEntry {
  const rank = overrides.rank ?? 1;
  return {
    rank,
    user_id: nextId(),
    username: `player${rank}`,
    avatar: null,
    total_games: 50,
    total_wins: 25,
    total_points: 5000,
    win_rate: 50,
    ...overrides,
  };
}

export function createTeamLeaderboardEntry(overrides: Partial<TeamLeaderboardEntry> = {}): TeamLeaderboardEntry {
  return {
    rank: 1,
    team_id: nextId(),
    name: 'Team Alpha',
    avatar: null,
    owner_name: 'captain',
    member_count: 5,
    total_points: 10000,
    total_games: 100,
    total_wins: 50,
    win_rate: 50,
    ...overrides,
  };
}

// ─── Social ────────────────────────────────────────────────────────────────

export function createFriend(overrides: Partial<Friend> = {}): Friend {
  return {
    friendship_id: nextId(),
    user: createUserMinimal(),
    since: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createFriendship(overrides: Partial<Friendship> = {}): Friendship {
  return {
    id: nextId(),
    from_user: createUserMinimal({ id: 1, username: 'sender' }),
    to_user: createUserMinimal({ id: 2, username: 'receiver' }),
    status: 'pending',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createPendingFriendRequest(overrides: Partial<PendingFriendRequest> = {}): PendingFriendRequest {
  return {
    id: nextId(),
    from_user: createUserMinimal(),
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createSocialNotification(overrides: Partial<SocialNotification> = {}): SocialNotification {
  return {
    id: nextUuid(),
    type: 'friend_request_accepted',
    message: 'user1 a accepté votre demande.',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

// ─── Team ──────────────────────────────────────────────────────────────────

export function createTeam(overrides: Partial<Team> = {}): Team {
  return {
    id: nextUuid(),
    name: 'Team Alpha',
    description: 'Une super équipe',
    avatar: null,
    owner: createUserMinimal({ id: 1, username: 'captain' }),
    members_list: [createTeamMember()],
    member_count: 1,
    total_games: 50,
    total_wins: 25,
    total_points: 5000,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-06-01T00:00:00Z',
    ...overrides,
  };
}

export function createTeamMember(overrides: Partial<TeamMember> = {}): TeamMember {
  return {
    id: nextId(),
    user: createUserMinimal(),
    role: 'member',
    joined_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

// ─── Achievement ───────────────────────────────────────────────────────────

export function createAchievement(overrides: Partial<Achievement> = {}): Achievement {
  const id = overrides.id ?? nextId();
  return {
    id,
    name: `Achievement ${id}`,
    description: 'Débloquez ce succès !',
    icon: null,
    points: 10,
    condition_type: 'games_played',
    condition_value: 10,
    unlocked: false,
    unlocked_at: null,
    ...overrides,
  };
}

export function createUserAchievement(overrides: Partial<UserAchievement> = {}): UserAchievement {
  return {
    id: nextId(),
    achievement: createAchievement({ unlocked: true, unlocked_at: '2024-06-01T00:00:00Z' }),
    unlocked_at: '2024-06-01T00:00:00Z',
    ...overrides,
  };
}

// ─── Shop ──────────────────────────────────────────────────────────────────

export function createShopItem(overrides: Partial<ShopItem> = {}): ShopItem {
  return {
    id: nextUuid(),
    name: 'Double Points',
    description: 'Double les points gagnés ce round',
    item_type: 'bonus',
    bonus_type: 'double_points',
    cost: 50,
    is_event_only: false,
    is_available: true,
    is_in_stock: true,
    sort_order: 1,
    ...overrides,
  };
}

export function createUserInventoryEntry(overrides: Partial<UserInventoryEntry> = {}): UserInventoryEntry {
  return {
    id: nextUuid(),
    item: createShopItem(),
    quantity: 1,
    purchased_at: '2024-06-01T00:00:00Z',
    ...overrides,
  };
}

export function createShopSummary(overrides: Partial<ShopSummary> = {}): ShopSummary {
  return {
    total_coins_available: 10000,
    user_balance: 500,
    items_count: 8,
    ...overrides,
  };
}

export function createGameBonus(overrides: Partial<GameBonus> = {}): GameBonus {
  return {
    id: nextUuid(),
    bonus_type: 'double_points',
    round_number: 1,
    activated_at: '2024-01-01T12:00:00Z',
    is_used: false,
    username: 'player1',
    ...overrides,
  };
}

// ─── Stats ─────────────────────────────────────────────────────────────────

export function createUserDetailedStats(overrides: Partial<UserDetailedStats> = {}): UserDetailedStats {
  return {
    total_games_played: 50,
    total_wins: 25,
    total_points: 5000,
    win_rate: 50,
    avg_score_per_game: 100,
    best_score: 500,
    total_correct_answers: 200,
    total_answers: 300,
    accuracy: 66.7,
    avg_response_time: 3.5,
    achievements_unlocked: 5,
    achievements_total: 20,
    recent_games: [],
    ...overrides,
  };
}

export function createUserPublicProfile(overrides: Partial<UserPublicProfile> = {}): UserPublicProfile {
  return {
    user_id: '1',
    username: 'testuser',
    avatar: null,
    date_joined: '2024-01-01T00:00:00Z',
    team: null,
    stats: createUserDetailedStats(),
    ...overrides,
  };
}

// ─── Playlist / YouTube ────────────────────────────────────────────────────

export function createYouTubePlaylist(overrides: Partial<YouTubePlaylist> = {}): YouTubePlaylist {
  return {
    youtube_id: `PL${nextId()}`,
    name: 'Test Playlist',
    description: 'A test playlist',
    image_url: 'https://example.com/image.jpg',
    total_tracks: 20,
    owner: 'TestOwner',
    external_url: 'https://youtube.com/playlist?list=PL1',
    ...overrides,
  };
}

export function createYouTubeTrack(overrides: Partial<YouTubeTrack> = {}): YouTubeTrack {
  return {
    youtube_id: `yt-${nextId()}`,
    name: 'Test Song',
    artists: ['Test Artist'],
    album: 'Test Album',
    album_image: 'https://example.com/album.jpg',
    duration_ms: 200000,
    preview_url: 'https://example.com/preview.mp3',
    external_url: 'https://youtube.com/watch?v=test',
    ...overrides,
  };
}

export function createKaraokeSong(overrides: Partial<KaraokeSong> = {}): KaraokeSong {
  return {
    id: nextId(),
    title: 'Bohemian Rhapsody',
    artist: 'Queen',
    youtube_video_id: 'fJ9rUzIMcZQ',
    lrclib_id: null,
    album_image_url: 'https://example.com/album.jpg',
    duration_ms: 354000,
    duration_display: '5:54',
    is_active: true,
    ...overrides,
  };
}

// ─── WebSocket ─────────────────────────────────────────────────────────────

export function createWebSocketMessage(overrides: Partial<WebSocketMessage> = {}): WebSocketMessage {
  return {
    type: 'test_message',
    ...overrides,
  };
}
