import { Avatar } from '@/components/ui';
import type { TeamLeaderboardEntry } from '@/types';
import { Link } from 'react-router-dom';

const MEDAL = ['🥇', '🥈', '🥉'];

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
        className={`px-4 py-2 rounded-xl text-sm font-medium border border-cream-300 transition-all ${
          page <= 1 ? 'opacity-30 cursor-not-allowed' : 'hover:bg-cream-200 text-dark-400 hover:text-dark'
        }`}
      >
        ← Précédent
      </button>
      <span className="text-dark-300 text-sm">
        {page} / {totalPages}
      </span>
      <button
        onClick={onNext}
        disabled={page >= totalPages}
        className={`px-4 py-2 rounded-xl text-sm font-medium border border-cream-300 transition-all ${
          page >= totalPages ? 'opacity-30 cursor-not-allowed' : 'hover:bg-cream-200 text-dark-400 hover:text-dark'
        }`}
      >
        Suivant →
      </button>
    </div>
  );
}

interface Props {
  teams: TeamLeaderboardEntry[];
  page: number;
  totalCount: number | null;
  pageSize: number;
  onPrev: () => void;
  onNext: () => void;
}

export default function TeamLeaderboard({ teams, page, totalCount, pageSize, onPrev, onNext }: Props) {
  return (
    <>
      {teams.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-dark-400 text-lg mb-4">Aucune équipe dans le classement</p>
          <Link
            to="/teams"
            className="px-5 py-2.5 rounded-xl font-semibold bg-primary-600 hover:bg-primary-500 border border-primary-500/50 text-white transition-all"
          >
            Créer une équipe
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-cream-300 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gradient-to-r from-primary-600 to-primary-500 text-xs uppercase tracking-wider border-b border-cream-300 text-white">
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
                    className={`border-t border-cream-200 transition-colors ${
                      isTop3 ? 'bg-cream-100' : 'hover:bg-cream-100'
                    }`}
                  >
                    <td className="text-center px-3 py-3">
                      {isTop3 ? (
                        <span className="text-lg">{MEDAL[idx]}</span>
                      ) : (
                        <span className="text-dark-300 text-sm font-medium">{idx + 1}</span>
                      )}
                    </td>
                    <td className="pr-3 py-3">
                      <div className="flex items-center gap-2.5">
                        <Avatar username={team.name} src={team.avatar} size="sm" />
                        <div className="min-w-0">
                          <Link
                            to={`/teams/${team.team_id}`}
                            className="font-medium text-dark truncate hover:underline block"
                          >
                            {team.name}
                          </Link>
                          {team.owner_name && (
                            <p className="text-[11px] text-dark-200">👑 {team.owner_name}</p>
                          )}
                          <p className="text-[11px] text-dark-200 sm:hidden">
                            {team.member_count} membres · {team.total_games} parties
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="text-center pr-3 py-3 hidden sm:table-cell text-dark-400">
                      {team.member_count}
                    </td>
                    <td className="text-center pr-3 py-3 hidden sm:table-cell text-dark-400">
                      {team.total_games}
                    </td>
                    <td className="text-center pr-3 py-3 hidden md:table-cell text-dark-400">
                      {team.total_wins}
                    </td>
                    <td className="text-center pr-3 py-3 hidden md:table-cell">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          team.win_rate >= 50
                            ? 'bg-primary-100 text-primary-600'
                            : 'bg-cream-200 text-dark-300'
                        }`}
                      >
                        {team.win_rate}%
                      </span>
                    </td>
                    <td className="text-right pr-5 py-3">
                      <span className="font-bold text-dark">{team.total_points.toLocaleString()}</span>
                      <span className="text-dark-200 text-xs ml-1">pts</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} totalCount={totalCount} pageSize={pageSize} onPrev={onPrev} onNext={onNext} />
    </>
  );
}
