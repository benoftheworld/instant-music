import { useState, useEffect, useCallback } from 'react';
import { getMediaUrl } from '@/services/api';
import { statsService } from '@/services/achievementService';
import { LEADERBOARD_TABS } from '@/constants/gameModes';
import { useAuthStore } from '@/store/authStore';
import type { LeaderboardEntry, TeamLeaderboardEntry, GameMode } from '@/types';
import { Link } from 'react-router-dom';

type LeaderboardTab = GameMode | 'general' | 'teams';

/* ── Helpers ───────────────────────────────────────────────────────── */

const MEDAL = ['🥇', '🥈', '🥉'];

function Avatar({
  name,
  avatar,
  size = 'md',
}: {
  name: string;
  avatar?: string | null;
  size?: 'sm' | 'md' | 'lg';
}) {
  const cls =
    size === 'lg'
      ? 'w-20 h-20 text-2xl'
      : size === 'sm'
      ? 'w-9 h-9 text-sm'
      : 'w-12 h-12 text-base';
  if (avatar) {
    return (
      <img
        src={getMediaUrl(avatar)}
        alt={name}
        className={`${cls} rounded-full object-cover ring-2 ring-white/20`}
      />
    );
  }
  return (
    <div
      className={`${cls} rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold ring-2 ring-white/20`}
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
}

/* ── Podium ────────────────────────────────────────────────────────── */

function Podium({ players }: { players: LeaderboardEntry[] }) {
  if (players.length < 3) return null;

  const positions = [
    { player: players[1], col: 0, height: 'h-28', ring: 'ring-slate-400', bar: 'from-slate-600 to-slate-400' },
    { player: players[0], col: 1, height: 'h-40', ring: 'ring-yellow-400', bar: 'from-yellow-600 to-yellow-400' },
    { player: players[2], col: 2, height: 'h-20', ring: 'ring-orange-400', bar: 'from-orange-600 to-orange-400' },
  ];

  return (
    <div className="flex items-end justify-center gap-3 sm:gap-5 mb-10">
      {positions.map(({ player, col, height, ring, bar }) => (
        <div key={col} className="flex flex-col items-center gap-1 w-28 sm:w-36">
          <span className="text-2xl sm:text-3xl">{col === 1 ? '👑' : MEDAL[col === 0 ? 1 : 2]}</span>
          <div className={`ring-2 ${ring} rounded-full`}>
            <Avatar name={player.username} avatar={player.avatar} size={col === 1 ? 'lg' : 'md'} />
          </div>
          <Link
            to={`/profile/${player.user_id}`}
            className={`font-bold truncate max-w-full hover:underline ${col === 1 ? 'text-yellow-300 text-base' : 'text-white/80 text-sm'}`}
          >
            {player.username}
          </Link>
          {player.team_name && player.team_id && (
            <Link to={`/teams/${player.team_id}`} className="text-[10px] text-white/40 hover:text-white/60 truncate max-w-full">
              {player.team_name}
            </Link>
          )}
          <div
            className={`w-full ${height} bg-gradient-to-t ${bar} rounded-t-xl flex flex-col items-center justify-center shadow-lg border-t-2 border-white/20`}
          >
            <p className={`font-extrabold text-white drop-shadow ${col === 1 ? 'text-2xl' : 'text-xl'}`}>
              {player.total_points.toLocaleString()}
            </p>
            <p className="text-white/50 text-[10px] uppercase">pts</p>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── PlayerTable ───────────────────────────────────────────────────── */

function PlayerTable({
  players,
  currentUserId,
}: {
  players: LeaderboardEntry[];
  currentUserId?: number | null;
}) {
  if (players.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-white/40 text-lg mb-4">Aucun joueur dans le classement</p>
        <Link
          to="/game/create"
          className="px-5 py-2.5 rounded-xl font-semibold bg-violet-600/80 hover:bg-violet-600 border border-violet-500/50 text-white transition-all"
        >
          Créer une partie
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-white/40 text-xs uppercase tracking-wider border-b border-white/10">
            <th className="text-center px-3 py-3 w-14">#</th>
            <th className="text-left pr-3 py-3">Joueur</th>
            <th className="text-center pr-3 py-3 hidden sm:table-cell w-20">Parties</th>
            <th className="text-center pr-3 py-3 hidden sm:table-cell w-24">Victoires</th>
            <th className="text-center pr-3 py-3 hidden md:table-cell w-20">Ratio</th>
            <th className="text-right pr-5 py-3 w-28">Points</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player, idx) => {
            const isMe = currentUserId != null && player.user_id === currentUserId;
            const isTop3 = idx < 3;
            return (
              <tr
                key={player.user_id}
                className={`border-t border-white/5 transition-colors ${
                  isMe
                    ? 'bg-violet-500/15 border-l-2 border-l-violet-400'
                    : isTop3
                    ? 'bg-white/[0.03]'
                    : 'hover:bg-white/[0.03]'
                }`}
              >
                <td className="text-center px-3 py-3">
                  {isTop3 ? (
                    <span className="text-lg">{MEDAL[idx]}</span>
                  ) : (
                    <span className="text-white/40 text-sm font-medium">{idx + 1}</span>
                  )}
                </td>
                <td className="pr-3 py-3">
                  <div className="flex items-center gap-2.5">
                    <Avatar name={player.username} avatar={player.avatar} size="sm" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Link
                          to={`/profile/${player.user_id}`}
                          className={`font-medium truncate hover:underline ${isMe ? 'text-violet-300' : 'text-white'}`}
                        >
                          {player.username}
                        </Link>
                        {isMe && (
                          <span className="text-[10px] bg-violet-500/40 text-violet-200 px-1.5 py-0.5 rounded-full font-semibold shrink-0">
                            VOUS
                          </span>
                        )}
                      </div>
                      {player.team_name && player.team_id && (
                        <Link
                          to={`/teams/${player.team_id}`}
                          className="text-[11px] text-white/30 hover:text-white/50 truncate block"
                        >
                          {player.team_name}
                        </Link>
                      )}
                      {/* Mobile stats */}
                      <p className="text-[11px] text-white/30 sm:hidden">
                        {player.total_games} parties · {player.total_wins} V · {player.win_rate}%
                      </p>
                    </div>
                  </div>
                </td>
                <td className="text-center pr-3 py-3 hidden sm:table-cell text-white/60">
                  {player.total_games}
                </td>
                <td className="text-center pr-3 py-3 hidden sm:table-cell text-white/60">
                  {player.total_wins}
                </td>
                <td className="text-center pr-3 py-3 hidden md:table-cell">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      player.win_rate >= 50
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-white/10 text-white/50'
                    }`}
                  >
                    {player.win_rate}%
                  </span>
                </td>
                <td className="text-right pr-5 py-3">
                  <span className="font-bold text-white">{player.total_points.toLocaleString()}</span>
                  <span className="text-white/30 text-xs ml-1">pts</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ── TeamTable ─────────────────────────────────────────────────────── */

function TeamTable({ teams }: { teams: TeamLeaderboardEntry[] }) {
  if (teams.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-white/40 text-lg mb-4">Aucune équipe dans le classement</p>
        <Link
          to="/teams"
          className="px-5 py-2.5 rounded-xl font-semibold bg-violet-600/80 hover:bg-violet-600 border border-violet-500/50 text-white transition-all"
        >
          Créer une équipe
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-white/40 text-xs uppercase tracking-wider border-b border-white/10">
            <th className="text-center px-3 py-3 w-14">#</th>
            <th className="text-left pr-3 py-3">Équipe</th>
            <th className="text-center pr-3 py-3 hidden sm:table-cell w-24">Membres</th>
            <th className="text-center pr-3 py-3 hidden sm:table-cell w-20">Parties</th>
            <th className="text-center pr-3 py-3 hidden md:table-cell w-24">Victoires</th>
            <th className="text-center pr-3 py-3 hidden md:table-cell w-20">Ratio</th>
            <th className="text-right pr-5 py-3 w-28">Points</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team, idx) => {
            const isTop3 = idx < 3;
            return (
              <tr
                key={team.team_id}
                className={`border-t border-white/5 transition-colors ${
                  isTop3 ? 'bg-white/[0.03]' : 'hover:bg-white/[0.03]'
                }`}
              >
                <td className="text-center px-3 py-3">
                  {isTop3 ? (
                    <span className="text-lg">{MEDAL[idx]}</span>
                  ) : (
                    <span className="text-white/40 text-sm font-medium">{idx + 1}</span>
                  )}
                </td>
                <td className="pr-3 py-3">
                  <div className="flex items-center gap-2.5">
                    {team.avatar ? (
                      <img
                        src={getMediaUrl(team.avatar)}
                        alt={team.name}
                        className="w-9 h-9 rounded-full object-cover ring-2 ring-white/20"
                      />
                    ) : (
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-sm ring-2 ring-white/20">
                        {team.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0">
                      <Link
                        to={`/teams/${team.team_id}`}
                        className="font-medium text-white truncate hover:underline block"
                      >
                        {team.name}
                      </Link>
                      {team.owner_name && (
                        <p className="text-[11px] text-white/30">👑 {team.owner_name}</p>
                      )}
                      <p className="text-[11px] text-white/30 sm:hidden">
                        {team.member_count} membres · {team.total_games} parties
                      </p>
                    </div>
                  </div>
                </td>
                <td className="text-center pr-3 py-3 hidden sm:table-cell text-white/60">
                  {team.member_count}
                </td>
                <td className="text-center pr-3 py-3 hidden sm:table-cell text-white/60">
                  {team.total_games}
                </td>
                <td className="text-center pr-3 py-3 hidden md:table-cell text-white/60">
                  {team.total_wins}
                </td>
                <td className="text-center pr-3 py-3 hidden md:table-cell">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      team.win_rate >= 50
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-white/10 text-white/50'
                    }`}
                  >
                    {team.win_rate}%
                  </span>
                </td>
                <td className="text-right pr-5 py-3">
                  <span className="font-bold text-white">{team.total_points.toLocaleString()}</span>
                  <span className="text-white/30 text-xs ml-1">pts</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ── Pagination ────────────────────────────────────────────────────── */

function Pagination({
  page,
  totalCount,
  pageSize,
  onPrev,
  onNext,
}: {
  page: number;
  totalCount: number | null;
  pageSize: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  if (totalCount === null || totalCount <= pageSize) return null;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  return (
    <div className="flex items-center justify-center gap-4 mt-6">
      <button
        onClick={onPrev}
        disabled={page <= 1}
        className={`px-4 py-2 rounded-xl text-sm font-medium border border-white/20 transition-all ${
          page <= 1 ? 'opacity-30 cursor-not-allowed' : 'hover:bg-white/10 text-white/70 hover:text-white'
        }`}
      >
        ← Précédent
      </button>
      <span className="text-white/40 text-sm">
        {page} / {totalPages}
      </span>
      <button
        onClick={onNext}
        disabled={page >= totalPages}
        className={`px-4 py-2 rounded-xl text-sm font-medium border border-white/20 transition-all ${
          page >= totalPages ? 'opacity-30 cursor-not-allowed' : 'hover:bg-white/10 text-white/70 hover:text-white'
        }`}
      >
        Suivant →
      </button>
    </div>
  );
}

/* ── Main page ─────────────────────────────────────────────────────── */

export default function LeaderboardPage() {
  const user = useAuthStore((s) => s.user);
  const [players, setPlayers] = useState<LeaderboardEntry[]>([]);
  const [teams, setTeams] = useState<TeamLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMode, setSelectedMode] = useState<LeaderboardTab>('general');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(50);
  const [totalCount, setTotalCount] = useState<number | null>(null);

  const fetchLeaderboard = useCallback(
    async (p: number) => {
      try {
        setLoading(true);
        setError(null);

        if (selectedMode === 'teams') {
          const data = await statsService.getTeamLeaderboard(p, pageSize);
          setTeams(data.results ?? []);
          setTotalCount(data.count ?? null);
          setPlayers([]);
        } else if (selectedMode === 'general') {
          const data = await statsService.getLeaderboard(p, pageSize);
          setPlayers(data.results ?? []);
          setTotalCount(data.count ?? null);
          setTeams([]);
        } else {
          const data = await statsService.getLeaderboardByMode(selectedMode, p, pageSize);
          setPlayers(data.results ?? []);
          setTotalCount(data.count ?? null);
          setTeams([]);
        }
      } catch (err) {
        console.error('Failed to fetch leaderboard:', err);
        setError('Impossible de charger le classement');
      } finally {
        setLoading(false);
      }
    },
    [selectedMode, pageSize],
  );

  useEffect(() => {
    setPage(1);
    fetchLeaderboard(1);
  }, [selectedMode, fetchLeaderboard]);

  const handlePrev = () => {
    if (page > 1) {
      const next = page - 1;
      setPage(next);
      fetchLeaderboard(next);
    }
  };
  const handleNext = () => {
    if (totalCount === null) return;
    const totalPages = Math.ceil(totalCount / pageSize);
    if (page < totalPages) {
      const next = page + 1;
      setPage(next);
      fetchLeaderboard(next);
    }
  };

  /* ── Separate primary / mode tabs ───────────────────────────── */
  const primaryTabs = LEADERBOARD_TABS.filter(
    (t) => t.value === 'general' || t.value === 'teams',
  );
  const modeTabs = LEADERBOARD_TABS.filter(
    (t) => t.value !== 'general' && t.value !== 'teams',
  );

  const subtitleMap: Record<string, string> = {
    general: 'Les meilleurs joueurs de tous les temps',
    teams: 'Les meilleures équipes — stats dédupliquées par partie',
    classique: 'Classement par points en mode Classique',
    rapide: 'Classement par points en mode Rapide',
    generation: 'Classement par points en mode Génération',
    paroles: 'Classement par points en mode Paroles',
    karaoke: 'Classement par points en mode Karaoké',
    mollo: 'Classement par points en mode Mollo',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] text-white">
      <div className="container mx-auto max-w-5xl px-4 py-10 space-y-8">
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">🏆 Classement</h1>
          <p className="text-white/40 text-sm sm:text-base">
            {subtitleMap[selectedMode] ?? ''}
          </p>
        </div>

        {/* ── Tabs ───────────────────────────────────────────── */}
        <div className="space-y-3">
          {/* Primary tabs */}
          <div className="flex justify-center gap-2">
            {primaryTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setSelectedMode(tab.value)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                  selectedMode === tab.value
                    ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/25'
                    : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white/80 border border-white/10'
                }`}
              >
                <span className="mr-1.5">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Mode tabs */}
          <div className="flex flex-wrap justify-center gap-1.5">
            {modeTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setSelectedMode(tab.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedMode === tab.value
                    ? 'bg-violet-500/80 text-white'
                    : 'bg-white/5 text-white/40 hover:bg-white/10 hover:text-white/60'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Content ────────────────────────────────────────── */}
        {loading ? (
          <div className="flex justify-center items-center py-24">
            <div className="animate-spin rounded-full h-10 w-10 border-2 border-white/20 border-t-violet-400" />
          </div>
        ) : error ? (
          <div className="text-center py-16">
            <p className="text-red-400">{error}</p>
          </div>
        ) : selectedMode === 'teams' ? (
          <>
            <TeamTable teams={teams} />
            <Pagination
              page={page}
              totalCount={totalCount}
              pageSize={pageSize}
              onPrev={handlePrev}
              onNext={handleNext}
            />
          </>
        ) : (
          <>
            <Podium players={players} />
            <PlayerTable players={players} currentUserId={user?.id} />
            <Pagination
              page={page}
              totalCount={totalCount}
              pageSize={pageSize}
              onPrev={handlePrev}
              onNext={handleNext}
            />
          </>
        )}
      </div>
    </div>
  );
}
