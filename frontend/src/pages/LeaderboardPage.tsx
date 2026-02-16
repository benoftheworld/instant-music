import { useState, useEffect } from 'react';
import { getMediaUrl } from '@/services/api';
import { statsService } from '@/services/achievementService';
import { LEADERBOARD_TABS } from '@/constants/gameModes';
import type { LeaderboardEntry, TeamLeaderboardEntry, GameMode } from '@/types';
import { Link } from 'react-router-dom';

type LeaderboardTab = GameMode | 'general' | 'teams';

export default function LeaderboardPage() {
  const [players, setPlayers] = useState<LeaderboardEntry[]>([]);
  const [teams, setTeams] = useState<TeamLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMode, setSelectedMode] = useState<LeaderboardTab>('general');

  useEffect(() => {
    fetchLeaderboard();
  }, [selectedMode]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (selectedMode === 'teams') {
        const data = await statsService.getTeamLeaderboard(100);
        setTeams(data);
        setPlayers([]);
      } else if (selectedMode === 'general') {
        const data = await statsService.getLeaderboard(100);
        setPlayers(data);
        setTeams([]);
      } else {
        const data = await statsService.getLeaderboardByMode(selectedMode, 100);
        setPlayers(data);
        setTeams([]);
      }
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err);
      setError('Impossible de charger le classement');
    } finally {
      setLoading(false);
    }
  };

  const getRankStyle = (index: number) => {
    switch (index) {
      case 0:
        return 'bg-gradient-to-r from-yellow-100 to-yellow-200 border-yellow-400';
      case 1:
        return 'bg-gradient-to-r from-gray-100 to-gray-200 border-gray-400';
      case 2:
        return 'bg-gradient-to-r from-orange-100 to-orange-200 border-orange-400';
      default:
        return 'bg-white border-gray-200';
    }
  };

  const getRankBadge = (index: number) => {
    switch (index) {
      case 0:
        return (
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center shadow-lg">
            <span className="text-2xl">🥇</span>
          </div>
        );
      case 1:
        return (
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center shadow-lg">
            <span className="text-2xl">🥈</span>
          </div>
        );
      case 2:
        return (
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-lg">
            <span className="text-2xl">🥉</span>
          </div>
        );
      default:
        return (
          <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-xl font-bold text-gray-700">{index + 1}</span>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold mb-2">🏆 Classement</h1>
        <p className="text-gray-600">
          {selectedMode === 'teams' ? 'Les meilleures équipes' : 'Les meilleurs joueurs de tous les temps'}
        </p>
      </div>

      {/* Mode Selector */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {LEADERBOARD_TABS.map((mode) => (
          <button
            key={mode.value}
            onClick={() => setSelectedMode(mode.value)}
            className={`px-3 py-2 rounded-lg font-medium transition-all text-sm ${
              selectedMode === mode.value
                ? 'bg-primary-500 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <span className="mr-1">{mode.icon}</span>
            {mode.label}
          </button>
        ))}
      </div>

      {/* Team Leaderboard */}
      {selectedMode === 'teams' ? (
        <TeamLeaderboard teams={teams} getRankStyle={getRankStyle} getRankBadge={getRankBadge} />
      ) : (
        <>
          {/* Top 3 Podium */}
          {players.length >= 3 && (
            <div className="mb-12">
              <div className="flex items-end justify-center gap-4 mb-4">
            {/* 2nd place */}
            <div className="flex flex-col items-center">
              <div className="relative w-20 h-20 mb-2">
                {players[1].avatar ? (
                  <img
                    src={getMediaUrl(players[1].avatar)}
                    alt={players[1].username}
                    className="w-full h-full rounded-full object-cover border-4 border-gray-400"
                  />
                ) : (
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-white text-2xl font-bold border-4 border-gray-400">
                    {players[1].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 text-2xl">🥈</div>
              </div>
              <p className="font-bold text-lg">{players[1].username}</p>
              {players[1].team_name && <p className="text-xs text-gray-400">🎯 {players[1].team_name}</p>}
              <p className="text-primary-600 font-semibold">{players[1].total_points.toLocaleString()} pts</p>
              <div className="w-28 h-32 bg-gradient-to-b from-gray-300 to-gray-500 rounded-t-lg mt-2 flex items-center justify-center">
                <span className="text-white text-4xl font-bold">2</span>
              </div>
            </div>

            {/* 1st place */}
            <div className="flex flex-col items-center">
              <div className="relative w-24 h-24 mb-2">
                {players[0].avatar ? (
                  <img
                    src={getMediaUrl(players[0].avatar)}
                    alt={players[0].username}
                    className="w-full h-full rounded-full object-cover border-4 border-yellow-400"
                  />
                ) : (
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center text-white text-3xl font-bold border-4 border-yellow-400">
                    {players[0].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 text-3xl animate-bounce">🥇</div>
              </div>
              <p className="font-bold text-xl">{players[0].username}</p>
              {players[0].team_name && <p className="text-xs text-gray-400">🎯 {players[0].team_name}</p>}
              <p className="text-primary-600 font-bold text-lg">{players[0].total_points.toLocaleString()} pts</p>
              <div className="w-28 h-44 bg-gradient-to-b from-yellow-300 to-yellow-500 rounded-t-lg mt-2 flex items-center justify-center">
                <span className="text-white text-5xl font-bold">1</span>
              </div>
            </div>

            {/* 3rd place */}
            <div className="flex flex-col items-center">
              <div className="relative w-20 h-20 mb-2">
                {players[2].avatar ? (
                  <img
                    src={getMediaUrl(players[2].avatar)}
                    alt={players[2].username}
                    className="w-full h-full rounded-full object-cover border-4 border-orange-400"
                  />
                ) : (
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-2xl font-bold border-4 border-orange-400">
                    {players[2].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 text-2xl">🥉</div>
              </div>
              <p className="font-bold text-lg">{players[2].username}</p>
              {players[2].team_name && <p className="text-xs text-gray-400">🎯 {players[2].team_name}</p>}
              <p className="text-primary-600 font-semibold">{players[2].total_points.toLocaleString()} pts</p>
              <div className="w-28 h-24 bg-gradient-to-b from-orange-400 to-orange-600 rounded-t-lg mt-2 flex items-center justify-center">
                <span className="text-white text-4xl font-bold">3</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {players.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">Aucun joueur dans le classement</p>
          <Link to="/game/create" className="btn-primary">
            Créer une partie
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Table header */}
          <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-3 bg-gray-100 rounded-lg font-semibold text-gray-600 text-sm">
            <div className="col-span-1">Rang</div>
            <div className="col-span-4">Joueur</div>
            <div className="col-span-2 text-center">Parties</div>
            <div className="col-span-2 text-center">Victoires</div>
            <div className="col-span-1 text-center">Ratio</div>
            <div className="col-span-2 text-right">Points</div>
          </div>

          {/* Player rows */}
          {players.map((player, index) => (
            <div
              key={player.user_id}
              className={`rounded-xl border-2 p-4 transition-all hover:shadow-lg ${getRankStyle(index)}`}
            >
              <div className="grid grid-cols-12 gap-4 items-center">
                {/* Rank */}
                <div className="col-span-2 md:col-span-1 flex justify-center">
                  {getRankBadge(index)}
                </div>

                {/* Player info */}
                <div className="col-span-10 md:col-span-4 flex items-center space-x-4">
                  {player.avatar ? (
                    <img
                      src={getMediaUrl(player.avatar)}
                      alt={player.username}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold text-lg">
                      {player.username.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <p className="font-bold text-lg">{player.username}</p>
                    {player.team_name && (
                      <p className="text-xs text-gray-400">🎯 {player.team_name}</p>
                    )}
                    <p className="text-sm text-gray-500 md:hidden">
                      {player.total_games} parties • {player.total_wins} victoires
                    </p>
                  </div>
                </div>

                {/* Stats (desktop) */}
                <div className="hidden md:block md:col-span-2 text-center">
                  <p className="font-semibold text-gray-700">{player.total_games}</p>
                </div>
                <div className="hidden md:block md:col-span-2 text-center">
                  <p className="font-semibold text-gray-700">{player.total_wins}</p>
                </div>
                <div className="hidden md:block md:col-span-1 text-center">
                  <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                    player.win_rate >= 50 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {player.win_rate}%
                  </span>
                </div>

                {/* Points */}
                <div className="col-span-12 md:col-span-2 text-center md:text-right">
                  <p className="text-2xl font-bold text-primary-600">
                    {player.total_points.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 uppercase">points</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
        </>
      )}
    </div>
  );
}

// Team Leaderboard Component
function TeamLeaderboard({
  teams,
  getRankStyle,
  getRankBadge,
}: {
  teams: TeamLeaderboardEntry[];
  getRankStyle: (index: number) => string;
  getRankBadge: (index: number) => JSX.Element;
}) {
  if (teams.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg mb-4">Aucune équipe dans le classement</p>
        <Link to="/teams" className="btn-primary">
          Créer une équipe
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Table header */}
      <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-3 bg-gray-100 rounded-lg font-semibold text-gray-600 text-sm">
        <div className="col-span-1">Rang</div>
        <div className="col-span-4">Équipe</div>
        <div className="col-span-2 text-center">Membres</div>
        <div className="col-span-2 text-center">Parties</div>
        <div className="col-span-1 text-center">Ratio</div>
        <div className="col-span-2 text-right">Points</div>
      </div>

      {/* Team rows */}
      {teams.map((team, index) => (
        <div
          key={team.team_id}
          className={`rounded-xl border-2 p-4 transition-all hover:shadow-lg ${getRankStyle(index)}`}
        >
          <div className="grid grid-cols-12 gap-4 items-center">
            {/* Rank */}
            <div className="col-span-2 md:col-span-1 flex justify-center">
              {getRankBadge(index)}
            </div>

            {/* Team info */}
            <div className="col-span-10 md:col-span-4 flex items-center space-x-4">
              {team.avatar ? (
                <img
                  src={getMediaUrl(team.avatar)}
                  alt={team.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-teal-500 flex items-center justify-center text-white font-bold text-lg">
                  {team.name.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <p className="font-bold text-lg">{team.name}</p>
                {team.owner_name && (
                  <p className="text-xs text-gray-400">👑 {team.owner_name}</p>
                )}
                <p className="text-sm text-gray-500 md:hidden">
                  {team.member_count} membres • {team.total_games} parties
                </p>
              </div>
            </div>

            {/* Stats (desktop) */}
            <div className="hidden md:block md:col-span-2 text-center">
              <p className="font-semibold text-gray-700">{team.member_count}</p>
            </div>
            <div className="hidden md:block md:col-span-2 text-center">
              <p className="font-semibold text-gray-700">{team.total_games}</p>
            </div>
            <div className="hidden md:block md:col-span-1 text-center">
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                team.win_rate >= 50 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {team.win_rate}%
              </span>
            </div>

            {/* Points */}
            <div className="col-span-12 md:col-span-2 text-center md:text-right">
              <p className="text-2xl font-bold text-primary-600">
                {team.total_points.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 uppercase">points</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
