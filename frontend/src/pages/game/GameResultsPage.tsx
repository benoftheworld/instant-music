import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BONUS_META } from '../../constants/bonuses';
import { Avatar } from '@/components/ui';
import type { BonusType, GamePlayer } from '@/types';
import { useGameResultsPage, type RoundDetail } from '../../hooks/pages/useGameResultsPage';

const MEDAL = ['🥇', '🥈', '🥉'];
const RANK_COLORS = [
  'from-yellow-100 to-yellow-50 border-yellow-400',
  'from-cream-200 to-cream-100 border-dark-200',
  'from-orange-100 to-orange-50 border-orange-400',
];

function RoundRow({ round, players }: { round: RoundDetail; players: GamePlayer[] }) {
  const [expanded, setExpanded] = useState(false);

  const playerUserId = (username: string) =>
    players.find((p) => p.username === username)?.user_id;

  // Sort answers by points earned desc for ranking
  const sorted = [...round.answers].sort((a, b) => b.points_earned - a.points_earned || a.response_time - b.response_time);
  const top3 = sorted.slice(0, 3);
  const rest = sorted.slice(3);

  const playerAvatar = (username: string) =>
    players.find((p) => p.username === username)?.avatar;

  const minTime = sorted.length > 0 ? Math.min(...sorted.map((a) => a.response_time)) : null;

  return (
    <div className="bg-white border border-cream-300 rounded-2xl overflow-hidden">
      {/* Round header */}
      <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-primary-600 to-primary-500 border-b border-cream-300 text-white">
        <div className="flex items-center gap-3">
          <span className="bg-primary-500 text-white text-xs font-bold px-2.5 py-1 rounded-full">
            Manche {round.round_number}
          </span>
          <span className="text-light font-semibold truncate max-w-xs">
            {round.track_name}
          </span>
          <span className="text-light-300 text-sm hidden sm:inline">— {round.artist_name}</span>
        </div>
        <span className="text-sm font-medium shrink-0">
          ✅ {round.correct_answer}
        </span>
      </div>

      {/* Bonus utilisés ce round */}
      {round.bonuses && round.bonuses.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-5 py-2 bg-cream-100 border-b border-cream-200">
          <span className="text-light-300 text-xs uppercase tracking-wider shrink-0">Bonus&nbsp;:</span>
          {round.bonuses.map((b, i) => {
            const meta = BONUS_META[b.bonus_type as BonusType];
            return (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs bg-cream-200 border border-cream-300 rounded-full px-2.5 py-0.5 text-dark-400"
                title={meta?.description}
              >
                <span aria-hidden="true">{meta?.emoji ?? '✨'}</span>
                <span className="font-semibold text-dark">{b.username}</span>
                <span className="text-dark-300">·</span>
                <span>{meta?.shortLabel ?? b.bonus_type}</span>
              </span>
            );
          })}
        </div>
      )}

      {/* Top-3 table */}
      {top3.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-300 text-xs uppercase tracking-wider">
                <th className="text-left pl-5 pr-3 py-2 w-12">#</th>
                <th className="text-left pr-3 py-2">Joueur</th>
                <th className="text-left pr-3 py-2 hidden sm:table-cell">Réponse</th>
                <th className="text-right pr-3 py-2">Pts</th>
                <th className="text-right pr-5 py-2 hidden md:table-cell">Temps</th>
              </tr>
            </thead>
            <tbody>
              {top3.map((ans, i) => {
                const isFastest = minTime !== null && ans.response_time === minTime;
                return (
                  <tr key={ans.username} className={`border-t border-cream-200 bg-gradient-to-r ${RANK_COLORS[i]} border-l-2`}>
                    <td className="pl-5 pr-3 py-2.5 text-xl w-12">{MEDAL[i]}</td>
                    <td className="pr-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Avatar username={ans.username} src={playerAvatar(ans.username)} size="sm" />
                        <span className="text-dark font-medium">
                          {playerUserId(ans.username) ? (
                            <Link to={`/profile/${playerUserId(ans.username)}`} className="hover:underline transition-colors">
                              {ans.username}
                            </Link>
                          ) : ans.username}
                        </span>
                        {isFastest && <span className="text-primary-600 text-xs">⚡</span>}
                      </div>
                    </td>
                    <td className="pr-3 py-2.5 hidden sm:table-cell">
                      <span className={ans.is_correct ? 'text-primary-600' : 'text-red-600'}>
                        {ans.is_correct ? '✓' : '✗'} {ans.answer}
                      </span>
                      {ans.streak_bonus !== undefined && ans.streak_bonus > 0 && (
                        <span className="ml-2 text-primary-400 text-xs">🔥×{ans.consecutive_correct}</span>
                      )}
                    </td>
                    <td className="pr-3 py-2.5 text-right font-bold text-dark">
                      +{ans.points_earned}
                    </td>
                    <td className="pr-5 py-2.5 text-right text-dark-300 hidden md:table-cell">
                      {ans.response_time.toFixed(1)}s
                    </td>
                  </tr>
                );
              })}

              {/* Expanded rows */}
              {expanded && rest.map((ans, i) => {
                const isFastest = minTime !== null && ans.response_time === minTime;
                return (
                  <tr key={ans.username} className="border-t border-cream-200">
                    <td className="pl-5 pr-3 py-2.5 text-dark-300 text-sm">{i + 4}.</td>
                    <td className="pr-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Avatar username={ans.username} src={playerAvatar(ans.username)} size="sm" />
                        <span className="text-dark-500 font-medium">
                          {playerUserId(ans.username) ? (
                            <Link to={`/profile/${playerUserId(ans.username)}`} className="hover:underline transition-colors">
                              {ans.username}
                            </Link>
                          ) : ans.username}
                        </span>
                        {isFastest && <span className="text-primary-600 text-xs">⚡</span>}
                      </div>
                    </td>
                    <td className="pr-3 py-2.5 hidden sm:table-cell">
                      <span className={ans.is_correct ? 'text-primary-500' : 'text-red-500'}>
                        {ans.is_correct ? '✓' : '✗'} {ans.answer}
                      </span>
                      {ans.streak_bonus !== undefined && ans.streak_bonus > 0 && (
                        <span className="ml-2 text-orange-300 text-xs">🔥×{ans.consecutive_correct}</span>
                      )}
                    </td>
                    <td className="pr-3 py-2.5 text-right font-bold text-dark-400">
                      +{ans.points_earned}
                    </td>
                    <td className="pr-5 py-2.5 text-right text-dark-300 hidden md:table-cell">
                      {ans.response_time.toFixed(1)}s
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-dark-200 text-sm px-5 py-4">Aucune réponse enregistrée</p>
      )}

      {/* Expand button */}
      {rest.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full py-2.5 text-dark-300 hover:text-dark text-xs font-medium border-t border-cream-200 transition-colors hover:bg-cream-100 flex items-center justify-center gap-1"
        >
          {expanded ? (
            <><span>↑ Masquer</span></>
          ) : (
            <><span>↓ Voir les {rest.length} autre{rest.length > 1 ? 's' : ''} joueur{rest.length > 1 ? 's' : ''}</span></>
          )}
        </button>
      )}
    </div>
  );
}

export default function GameResultsPage() {
  const {
    roomCode,
    navigate,
    results,
    loading,
    downloadingPdf,
    showFullRanking,
    setShowFullRanking,
    handleDownloadPdf,
    game,
    rankings,
    rounds,
    top3,
    others,
    winner,
    podiumOrder,
  } = useGameResultsPage();

  if (loading) {
    return (
      <div className="min-h-screen bg-cream-100 flex items-center justify-center">
        <div className="text-dark-400 text-xl animate-pulse">Chargement des résultats…</div>
      </div>
    );
  }

  if (!results || !game) {
    return (
      <div className="min-h-screen bg-cream-100 flex items-center justify-center">
        <div className="text-dark-400 text-xl">Résultats introuvables</div>
      </div>
    );
  }

  const podiumHeights = ['h-32', 'h-48', 'h-24'];
  const podiumPos = [1, 0, 2];

  return (
    <div className="min-h-screen bg-cream-100 text-dark">
      <div className="container mx-auto max-w-5xl px-4 py-10 space-y-12">

        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Partie terminée !</h1>
          <p className="text-dark-400 text-lg">Salle {roomCode}</p>
          <div className="flex flex-wrap justify-center gap-2 mt-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary-100 border border-primary-300 text-primary-700">
              {game.mode_display}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary-100 border border-primary-300 text-primary-700">
              {game.answer_mode === 'mcq' ? '📋 QCM' : '⌨️ Saisie libre'}
            </span>
            {(game.mode === 'classique' || game.mode === 'rapide') && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary-100 border border-primary-300 text-primary-700">
                {game.guess_target === 'artist' ? '🎤 Artiste' : '🎵 Titre'}
              </span>
            )}
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cream-300 border border-cream-400 text-dark-400">
              {game.num_rounds} manches
            </span>
          </div>
        </div>

        {/* ── Podium ─────────────────────────────────────────────── */}
        {top3.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-center text-2xl font-bold text-dark-500">🏆 Podium</h2>
            <div className="flex items-end justify-center gap-3 sm:gap-6">
              {podiumOrder.map((player, colIdx) => {
                if (!player) return <div key={colIdx} className="w-28 sm:w-36" />;
                const pos = podiumPos[colIdx]; // 0=1st,1=2nd,2=3rd
                const isWinner = pos === 0;
                const borderColors = ['border-yellow-400', 'border-dark-200', 'border-orange-400'];
                const glowColors = ['shadow-yellow-500/20', 'shadow-dark-200/20', 'shadow-orange-500/20'];
                const barColors = [
                  'bg-gradient-to-t from-yellow-600 to-yellow-400',
                  'bg-gradient-to-t from-slate-600 to-slate-400',
                  'bg-gradient-to-t from-orange-600 to-orange-400',
                ];
                return (
                  <div key={player.id} className="flex flex-col items-center gap-1">
                    <span className="text-3xl sm:text-4xl">{isWinner ? '👑' : MEDAL[pos]}</span>
                    <Avatar username={player.username} src={player.avatar} size={isWinner ? 'lg' : 'md'} />
                    <p className={`font-bold mt-1 ${isWinner ? 'text-lg text-primary-600' : 'text-sm text-dark-500'}`}>
                      {player.user_id ? (
                        <Link to={`/profile/${player.user_id}`} className="hover:underline transition-colors">
                          {player.username}
                        </Link>
                      ) : player.username}
                    </p>
                    <div className={`w-28 sm:w-36 ${podiumHeights[colIdx]} ${barColors[pos]} rounded-t-xl flex flex-col items-center justify-center shadow-lg ${glowColors[pos]} border-t-4 ${borderColors[pos]}`}>
                      <p className={`font-extrabold ${isWinner ? 'text-3xl' : 'text-2xl'} text-white drop-shadow`}>
                        {player.score}
                      </p>
                      <p className="text-white/60 text-xs">pts</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Classement complet ─────────────────────────────────── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-dark-500">📊 Classement</h2>
            {others.length > 0 && (
              <button
                onClick={() => setShowFullRanking(!showFullRanking)}
                className="text-xs text-dark-300 hover:text-dark border border-cream-300 hover:border-cream-400 px-3 py-1.5 rounded-lg transition-colors"
              >
                {showFullRanking ? '↑ Masquer' : `↓ Voir tous (${rankings.length})`}
              </button>
            )}
          </div>
          <div className="bg-white border border-cream-300 rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gradient-to-r from-primary-600 to-primary-500 text-xs uppercase tracking-wider border-b border-cream-300 text-white">
                  <th className="text-center pl-5 pr-3 py-3 w-12">#</th>
                  <th className="text-left pr-3 py-3">Joueur</th>
                  <th className="text-right pr-5 py-3">Score</th>
                </tr>
              </thead>
              <tbody>
                {(showFullRanking ? rankings : top3).map((player, idx) => {
                  const isWinner = idx === 0;
                  return (
                    <tr key={player.id} className={`border-t border-cream-200 ${isWinner ? 'bg-primary-50' : ''}`}>
                      <td className="text-center pl-5 pr-3 py-3 text-xl">
                        {idx < 3 ? MEDAL[idx] : <span className="text-white/40 text-sm">{idx + 1}.</span>}
                      </td>
                      <td className="pr-3 py-3">
                        <div className="flex items-center gap-2.5">
                          <Avatar username={player.username} src={player.avatar} size="sm" />
                          <span className={`font-medium ${isWinner ? 'text-primary-600' : 'text-dark'}`}>
                            {player.user_id ? (
                              <Link to={`/profile/${player.user_id}`} className="hover:underline transition-colors">
                                {player.username}
                              </Link>
                            ) : player.username}
                          </span>
                        </div>
                      </td>
                      <td className="pr-5 py-3 text-right font-bold text-dark">
                        {player.score} <span className="text-dark-300 font-normal text-xs">pts</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {!showFullRanking && others.length > 0 && (
              <button
                onClick={() => setShowFullRanking(true)}
                className="w-full py-3 text-dark-300 hover:text-dark text-xs font-medium border-t border-cream-200 transition-colors hover:bg-cream-100"
              >
                ↓ + {others.length} autre{others.length > 1 ? 's' : ''} joueur{others.length > 1 ? 's' : ''}
              </button>
            )}
          </div>

          {/* Mise en avant du gagnant */}
          {winner && (
            <div className="flex items-center gap-4 bg-primary-50 border border-primary-300 rounded-2xl px-5 py-3">
              <span className="text-3xl">👑</span>
              <div>
                <p className="text-primary-600 font-bold text-lg">
                  {winner.user_id ? (
                    <Link to={`/profile/${winner.user_id}`} className="hover:underline transition-colors">
                      {winner.username}
                    </Link>
                  ) : winner.username}
                </p>
                <p className="text-dark-400 text-sm">remporte la partie avec {winner.score} pts</p>
              </div>
            </div>
          )}
        </div>

        {/* ── Détail par manche ───────────────────────────────────── */}
        {rounds.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-dark-500">🎵 Détail par manche</h2>
            <div className="space-y-3">
              {rounds.map((round) => (
                <RoundRow key={round.round_number} round={round} players={rankings} />
              ))}
            </div>
          </div>
        )}

        {/* ── Actions ────────────────────────────────────────────── */}
        <div className="flex flex-wrap justify-center gap-3 pb-8">
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2.5 rounded-xl font-semibold border-2 border-dark text-dark hover:bg-dark hover:text-cream-100 transition-all"
          >
            ← Accueil
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="px-6 py-2.5 rounded-xl font-semibold bg-primary-600 hover:bg-primary-700 border border-primary-500 transition-all text-white disabled:opacity-50 flex items-center gap-2"
          >
            {downloadingPdf ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Génération…
              </>
            ) : (
              '📄 Télécharger PDF'
            )}
          </button>
          <button
            onClick={() => navigate('/game/create')}
            className="px-6 py-2.5 rounded-xl font-semibold bg-primary-600 hover:bg-primary-700 border border-primary-500 transition-all text-white"
          >
            + Nouvelle partie
          </button>
        </div>

      </div>
    </div>
  );
}
