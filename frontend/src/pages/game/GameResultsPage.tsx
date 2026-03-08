import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { getMediaUrl } from '../../services/api';
import { BONUS_META } from '../../constants/bonuses';
import type { BonusType, GamePlayer } from '@/types';

interface RoundAnswer {
  username: string;
  answer: string;
  is_correct: boolean;
  points_earned: number;
  response_time: number;
  consecutive_correct?: number;
  streak_bonus?: number;
}

interface RoundBonus {
  username: string;
  bonus_type: string;
}

interface RoundDetail {
  round_number: number;
  track_name: string;
  artist_name: string;
  correct_answer: string;
  track_id: string;
  answers: RoundAnswer[];
  bonuses: RoundBonus[];
}

interface GameResult {
  game: {
    id: string;
    room_code: string;
    host: number;
    status: string;
    mode: string;
    mode_display: string;
    answer_mode: string;
    answer_mode_display: string;
    guess_target: string;
    guess_target_display: string;
    num_rounds: number;
    is_party_mode: boolean;
  };
  rankings: GamePlayer[];
  rounds: RoundDetail[];
}

const MEDAL = ['🥇', '🥈', '🥉'];
const RANK_COLORS = [
  'from-yellow-400/20 to-yellow-600/10 border-yellow-400/40',
  'from-slate-300/20 to-slate-500/10 border-slate-400/40',
  'from-orange-400/20 to-orange-600/10 border-orange-400/40',
];

function Avatar({ username, avatar, size = 'md' }: { username: string; avatar?: string; size?: 'sm' | 'md' | 'lg' }) {
  const cls = size === 'lg' ? 'w-24 h-24 text-3xl' : size === 'sm' ? 'w-8 h-8 text-xs' : 'w-11 h-11 text-base';
  if (avatar) {
    return <img src={getMediaUrl(avatar)} alt={username} className={`${cls} rounded-full object-cover ring-2 ring-white/20`} />;
  }
  return (
    <div className={`${cls} rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold ring-2 ring-white/20`}>
      {username.charAt(0).toUpperCase()}
    </div>
  );
}

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
    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
      {/* Round header */}
      <div className="flex items-center justify-between px-5 py-3 bg-white/5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <span className="bg-violet-500/80 text-white text-xs font-bold px-2.5 py-1 rounded-full">
            Round {round.round_number}
          </span>
          <span className="text-white font-semibold truncate max-w-xs">
            {round.track_name}
          </span>
          <span className="text-white/50 text-sm hidden sm:inline">— {round.artist_name}</span>
        </div>
        <span className="text-emerald-400 text-sm font-medium shrink-0">
          ✅ {round.correct_answer}
        </span>
      </div>

      {/* Bonus utilisés ce round */}
      {round.bonuses && round.bonuses.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-5 py-2 bg-amber-400/5 border-b border-white/5">
          <span className="text-white/30 text-xs uppercase tracking-wider shrink-0">Bonus&nbsp;:</span>
          {round.bonuses.map((b, i) => {
            const meta = BONUS_META[b.bonus_type as BonusType];
            return (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs bg-white/10 border border-white/10 rounded-full px-2.5 py-0.5 text-white/80"
                title={meta?.description}
              >
                <span aria-hidden="true">{meta?.emoji ?? '✨'}</span>
                <span className="font-semibold text-white">{b.username}</span>
                <span className="text-white/50">·</span>
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
              <tr className="text-white/40 text-xs uppercase tracking-wider">
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
                  <tr key={ans.username} className={`border-t border-white/5 bg-gradient-to-r ${RANK_COLORS[i]} border-l-2`}>
                    <td className="pl-5 pr-3 py-2.5 text-xl w-12">{MEDAL[i]}</td>
                    <td className="pr-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Avatar username={ans.username} avatar={playerAvatar(ans.username)} size="sm" />
                        <span className="text-white font-medium">
                          {playerUserId(ans.username) ? (
                            <Link to={`/profile/${playerUserId(ans.username)}`} className="hover:underline transition-colors">
                              {ans.username}
                            </Link>
                          ) : ans.username}
                        </span>
                        {isFastest && <span className="text-yellow-300 text-xs">⚡</span>}
                      </div>
                    </td>
                    <td className="pr-3 py-2.5 hidden sm:table-cell">
                      <span className={ans.is_correct ? 'text-emerald-400' : 'text-red-400'}>
                        {ans.is_correct ? '✓' : '✗'} {ans.answer}
                      </span>
                      {ans.streak_bonus !== undefined && ans.streak_bonus > 0 && (
                        <span className="ml-2 text-orange-300 text-xs">🔥×{ans.consecutive_correct}</span>
                      )}
                    </td>
                    <td className="pr-3 py-2.5 text-right font-bold text-white">
                      +{ans.points_earned}
                    </td>
                    <td className="pr-5 py-2.5 text-right text-white/50 hidden md:table-cell">
                      {ans.response_time.toFixed(1)}s
                    </td>
                  </tr>
                );
              })}

              {/* Expanded rows */}
              {expanded && rest.map((ans, i) => {
                const isFastest = minTime !== null && ans.response_time === minTime;
                return (
                  <tr key={ans.username} className="border-t border-white/5">
                    <td className="pl-5 pr-3 py-2.5 text-white/40 text-sm">{i + 4}.</td>
                    <td className="pr-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Avatar username={ans.username} avatar={playerAvatar(ans.username)} size="sm" />
                        <span className="text-white/80 font-medium">
                          {playerUserId(ans.username) ? (
                            <Link to={`/profile/${playerUserId(ans.username)}`} className="hover:underline transition-colors">
                              {ans.username}
                            </Link>
                          ) : ans.username}
                        </span>
                        {isFastest && <span className="text-yellow-300 text-xs">⚡</span>}
                      </div>
                    </td>
                    <td className="pr-3 py-2.5 hidden sm:table-cell">
                      <span className={ans.is_correct ? 'text-emerald-400/80' : 'text-red-400/60'}>
                        {ans.is_correct ? '✓' : '✗'} {ans.answer}
                      </span>
                      {ans.streak_bonus !== undefined && ans.streak_bonus > 0 && (
                        <span className="ml-2 text-orange-300 text-xs">🔥×{ans.consecutive_correct}</span>
                      )}
                    </td>
                    <td className="pr-3 py-2.5 text-right font-bold text-white/70">
                      +{ans.points_earned}
                    </td>
                    <td className="pr-5 py-2.5 text-right text-white/40 hidden md:table-cell">
                      {ans.response_time.toFixed(1)}s
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-white/30 text-sm px-5 py-4">Aucune réponse enregistrée</p>
      )}

      {/* Expand button */}
      {rest.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full py-2.5 text-white/50 hover:text-white/80 text-xs font-medium border-t border-white/10 transition-colors hover:bg-white/5 flex items-center justify-center gap-1"
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
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<GameResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [showFullRanking, setShowFullRanking] = useState(false);

  useEffect(() => {
    const loadResults = async () => {
      if (!roomCode) return;
      try {
        const data = await gameService.getResults(roomCode);
        setResults(data as unknown as GameResult);
      } catch (error) {
        console.error('Failed to load results:', error);
      } finally {
        setLoading(false);
      }
    };
    loadResults();
  }, [roomCode]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] flex items-center justify-center">
        <div className="text-white/70 text-xl animate-pulse">Chargement des résultats…</div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] flex items-center justify-center">
        <div className="text-white/70 text-xl">Résultats introuvables</div>
      </div>
    );
  }

  const { rankings: rawRankings, rounds, game } = results;

  // En mode soirée, exclure le présentateur (hôte) du classement
  const rankings = game.is_party_mode
    ? rawRankings.filter(p => String(p.user_id) !== String(game.host))
    : rawRankings;

  const top3 = rankings.slice(0, 3);
  const others = rankings.slice(3);
  const winner = rankings[0];

  const podiumOrder = [
    top3[1] ?? null,  // 2nd — left
    top3[0] ?? null,  // 1st — center
    top3[2] ?? null,  // 3rd — right
  ];
  const podiumHeights = ['h-32', 'h-48', 'h-24'];
  const podiumPos = [1, 0, 2]; // index into top3

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] text-white">
      <div className="container mx-auto max-w-5xl px-4 py-10 space-y-12">

        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="text-center space-y-4">
          <div className="text-6xl animate-bounce inline-block">🎉</div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Partie terminée !</h1>
          <p className="text-white/50 text-lg">Salle {roomCode}</p>
          <div className="flex flex-wrap justify-center gap-2 mt-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-500/30 border border-violet-400/40 text-violet-200">
              {game.mode_display}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/30 border border-blue-400/40 text-blue-200">
              {game.answer_mode === 'mcq' ? '📋 QCM' : '⌨️ Saisie libre'}
            </span>
            {(game.mode === 'classique' || game.mode === 'rapide') && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-pink-500/30 border border-pink-400/40 text-pink-200">
                {game.guess_target === 'artist' ? '🎤 Artiste' : '🎵 Titre'}
              </span>
            )}
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 border border-white/20 text-white/70">
              {game.num_rounds} rounds
            </span>
          </div>
        </div>

        {/* ── Podium ─────────────────────────────────────────────── */}
        {top3.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-center text-2xl font-bold text-white/80">🏆 Podium</h2>
            <div className="flex items-end justify-center gap-3 sm:gap-6">
              {podiumOrder.map((player, colIdx) => {
                if (!player) return <div key={colIdx} className="w-28 sm:w-36" />;
                const pos = podiumPos[colIdx]; // 0=1st,1=2nd,2=3rd
                const isWinner = pos === 0;
                const borderColors = ['border-yellow-400', 'border-slate-400', 'border-orange-400'];
                const glowColors = ['shadow-yellow-500/30', 'shadow-slate-400/20', 'shadow-orange-500/20'];
                const barColors = [
                  'bg-gradient-to-t from-yellow-600 to-yellow-400',
                  'bg-gradient-to-t from-slate-600 to-slate-400',
                  'bg-gradient-to-t from-orange-600 to-orange-400',
                ];
                return (
                  <div key={player.id} className="flex flex-col items-center gap-1">
                    <span className="text-3xl sm:text-4xl">{isWinner ? '👑' : MEDAL[pos]}</span>
                    <Avatar username={player.username} avatar={player.avatar} size={isWinner ? 'lg' : 'md'} />
                    <p className={`font-bold mt-1 ${isWinner ? 'text-lg text-yellow-300' : 'text-sm text-white/80'}`}>
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
            <h2 className="text-xl font-bold text-white/80">📊 Classement</h2>
            {others.length > 0 && (
              <button
                onClick={() => setShowFullRanking(!showFullRanking)}
                className="text-xs text-white/50 hover:text-white/80 border border-white/20 hover:border-white/40 px-3 py-1.5 rounded-lg transition-colors"
              >
                {showFullRanking ? '↑ Masquer' : `↓ Voir tous (${rankings.length})`}
              </button>
            )}
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/40 text-xs uppercase tracking-wider border-b border-white/10">
                  <th className="text-center pl-5 pr-3 py-3 w-12">#</th>
                  <th className="text-left pr-3 py-3">Joueur</th>
                  <th className="text-right pr-5 py-3">Score</th>
                </tr>
              </thead>
              <tbody>
                {(showFullRanking ? rankings : top3).map((player, idx) => {
                  const isWinner = idx === 0;
                  return (
                    <tr key={player.id} className={`border-t border-white/5 ${isWinner ? 'bg-yellow-400/10' : ''}`}>
                      <td className="text-center pl-5 pr-3 py-3 text-xl">
                        {idx < 3 ? MEDAL[idx] : <span className="text-white/40 text-sm">{idx + 1}.</span>}
                      </td>
                      <td className="pr-3 py-3">
                        <div className="flex items-center gap-2.5">
                          <Avatar username={player.username} avatar={player.avatar} size="sm" />
                          <span className={`font-medium ${isWinner ? 'text-yellow-300' : 'text-white'}`}>
                            {player.user_id ? (
                              <Link to={`/profile/${player.user_id}`} className="hover:underline transition-colors">
                                {player.username}
                              </Link>
                            ) : player.username}
                          </span>
                        </div>
                      </td>
                      <td className="pr-5 py-3 text-right font-bold text-white">
                        {player.score} <span className="text-white/40 font-normal text-xs">pts</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {!showFullRanking && others.length > 0 && (
              <button
                onClick={() => setShowFullRanking(true)}
                className="w-full py-3 text-white/40 hover:text-white/70 text-xs font-medium border-t border-white/10 transition-colors hover:bg-white/5"
              >
                ↓ + {others.length} autre{others.length > 1 ? 's' : ''} joueur{others.length > 1 ? 's' : ''}
              </button>
            )}
          </div>

          {/* Mise en avant du gagnant */}
          {winner && (
            <div className="flex items-center gap-4 bg-yellow-400/10 border border-yellow-400/30 rounded-2xl px-5 py-3">
              <span className="text-3xl">👑</span>
              <div>
                <p className="text-yellow-300 font-bold text-lg">
                  {winner.user_id ? (
                    <Link to={`/profile/${winner.user_id}`} className="hover:underline transition-colors">
                      {winner.username}
                    </Link>
                  ) : winner.username}
                </p>
                <p className="text-white/50 text-sm">remporte la partie avec {winner.score} pts</p>
              </div>
            </div>
          )}
        </div>

        {/* ── Détail par round ───────────────────────────────────── */}
        {rounds.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white/80">🎵 Détail par round</h2>
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
            className="px-6 py-2.5 rounded-xl font-semibold bg-white/10 hover:bg-white/20 border border-white/20 hover:border-white/40 transition-all text-white"
          >
            ← Accueil
          </button>
          <button
            onClick={async () => {
              if (!roomCode) return;
              setDownloadingPdf(true);
              try {
                await gameService.downloadResultsPdf(roomCode);
              } catch (e) {
                console.error('PDF download failed:', e);
              } finally {
                setDownloadingPdf(false);
              }
            }}
            disabled={downloadingPdf}
            className="px-6 py-2.5 rounded-xl font-semibold bg-emerald-600/80 hover:bg-emerald-600 border border-emerald-500/50 transition-all text-white disabled:opacity-50 flex items-center gap-2"
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
            className="px-6 py-2.5 rounded-xl font-semibold bg-violet-600/80 hover:bg-violet-600 border border-violet-500/50 transition-all text-white"
          >
            + Nouvelle partie
          </button>
        </div>

      </div>
    </div>
  );
}
