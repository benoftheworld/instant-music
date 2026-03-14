/**
 * Fixtures : données de test pré-remplies pour le mock DB.
 */
import { createUser, createGame, createGamePlayer, createGameHistory, createLeaderboardEntry, createTeamLeaderboardEntry, createAchievement, createUserAchievement, createFriend, createFriendship, createPendingFriendRequest, createGameInvitation, createTeam, createShopItem, createUserInventoryEntry, createGameBonus, createUserDetailedStats, createUserPublicProfile, createYouTubePlaylist, createYouTubeTrack, createKaraokeSong } from '@/tests/shared/factories';
import type { MockDB } from './db';

export function createSeededDB(): Partial<MockDB> {
  const user1 = createUser({ id: 1, username: 'alice', email: 'alice@test.com' });
  const user2 = createUser({ id: 2, username: 'bob', email: 'bob@test.com' });
  const user3 = createUser({ id: 3, username: 'charlie', email: 'charlie@test.com' });

  const game1 = createGame({ room_code: 'ABC123', host: 1, host_username: 'alice', status: 'waiting' });
  const game2 = createGame({ room_code: 'DEF456', host: 2, host_username: 'bob', status: 'in_progress' });

  const player1 = createGamePlayer({ id: 1, username: 'alice', score: 300 });
  const player2 = createGamePlayer({ id: 2, username: 'bob', score: 250 });
  const player3 = createGamePlayer({ id: 3, username: 'charlie', score: 100 });

  const users = new Map<number, typeof user1>();
  users.set(1, user1);
  users.set(2, user2);
  users.set(3, user3);

  const games = new Map<string, typeof game1>();
  games.set('ABC123', { ...game1, players: [player1, player2] });
  games.set('DEF456', { ...game2, players: [player2, player3] });

  const gamePlayers = new Map<string, typeof player1[]>();
  gamePlayers.set('ABC123', [player1, player2]);
  gamePlayers.set('DEF456', [player2, player3]);

  return {
    users,
    games,
    gamePlayers,
    currentUser: user1,
    accessToken: 'mock-access-token-valid',
    refreshToken: 'mock-refresh-token-valid',
    gameHistory: [
      createGameHistory({ id: '1', room_code: 'ABC123', host_username: 'alice' }),
      createGameHistory({ id: '2', room_code: 'DEF456', host_username: 'bob' }),
    ],
    leaderboard: [
      createLeaderboardEntry({ rank: 1, user_id: 1, username: 'alice', total_points: 1500 }),
      createLeaderboardEntry({ rank: 2, user_id: 2, username: 'bob', total_points: 1200 }),
      createLeaderboardEntry({ rank: 3, user_id: 3, username: 'charlie', total_points: 800 }),
    ],
    teamLeaderboard: [
      createTeamLeaderboardEntry({ rank: 1, team_id: 1, name: 'Team Alpha', total_points: 5000 }),
    ],
    achievements: [
      createAchievement({ id: 1, name: 'Premier pas', unlocked: true }),
      createAchievement({ id: 2, name: 'Série de victoires', unlocked: false }),
    ],
    userAchievements: [
      createUserAchievement({ id: 1 }),
    ],
    friends: [
      createFriend({ friendship_id: 1, user: { id: 2, username: 'bob', avatar: null, total_points: 1200, total_wins: 8 } }),
    ],
    friendships: [
      createFriendship({ id: 1 }),
      createPendingFriendRequest({ id: 2 }),
    ],
    invitations: [
      createGameInvitation({ id: 'inv-1', room_code: 'ABC123' }),
    ],
    teams: [
      createTeam({ id: 'team-1', name: 'Team Alpha' }),
    ],
    shopItems: [
      createShopItem({ id: 'item-1', name: 'Double Points', bonus_type: 'double_points', cost: 100 }),
      createShopItem({ id: 'item-2', name: '50/50', bonus_type: 'fifty_fifty', cost: 150 }),
    ],
    inventory: [
      createUserInventoryEntry({ id: 'inv-1', quantity: 2 }),
    ],
    gameBonuses: [
      createGameBonus({ id: 'bonus-1', bonus_type: 'double_points' }),
    ],
    shopSummary: { total_coins_available: 1000, user_balance: 500, items_count: 5 },
    userStats: createUserDetailedStats(),
    publicProfiles: new Map([
      ['2', createUserPublicProfile({ user_id: '2', username: 'bob' })],
    ]),
    playlists: [
      createYouTubePlaylist({ youtube_id: 'PLtest1', name: 'Test Playlist' }),
    ],
    tracks: new Map([
      ['PLtest1', [createYouTubeTrack({ youtube_id: 'vid1', name: 'Track 1' }), createYouTubeTrack({ youtube_id: 'vid2', name: 'Track 2' })]],
    ]),
    karaokeSongs: [
      createKaraokeSong({ id: 1, title: 'Bohemian Rhapsody', artist: 'Queen' }),
    ],
    leaderboardResponse: {
      results: [
        createLeaderboardEntry({ rank: 1, user_id: 1, username: 'alice', total_points: 1500 }),
        createLeaderboardEntry({ rank: 2, user_id: 2, username: 'bob', total_points: 1200 }),
      ],
      count: 2,
      page: 1,
      page_size: 50,
    },
    teamLeaderboardResponse: {
      results: [
        createTeamLeaderboardEntry({ rank: 1, team_id: 1, name: 'Team Alpha', total_points: 5000 }),
      ],
      count: 1,
      page: 1,
      page_size: 50,
    },
  };
}
