import { formatAnswer } from '@/utils/formatAnswer';
import { useAudioPlayerOnResults } from './shared';
import { BONUS_META } from '@/constants/bonuses';
import { Avatar } from '@/components/ui';
import type { GameRound, GamePlayer, BonusType } from '@/types';

/** Per-player score data for the current round (from backend round_ended event) */
interface PlayerRoundScore {
  points_earned: number;
  is_correct: boolean;
  response_time: number;
  streak_bonus?: number;
  consecutive_correct?: number;
}

interface RoundBonusInfo {
  username: string;
  bonus_type: string;
}

interface RoundResultsScreenProps {
  round: GameRound;
  players: GamePlayer[];
  correctAnswer: string;
  myPointsEarned: number;
  /** The answer the current player submitted (null if no answer) */
  myAnswer?: string | null;
  /** Per-player round scores keyed by username */
  playerScores?: Record<string, PlayerRoundScore>;
  /** Bonuses activated during this round */
  roundBonuses?: RoundBonusInfo[];
  onContinue?: () => void;
}

/** Generate a human-readable description for a bonus */
function describeBonusImpact(bonus: RoundBonusInfo): string {
  const meta = BONUS_META[bonus.bonus_type as BonusType];
  if (!meta) return `${bonus.username} a utilisé un bonus`;

  switch (bonus.bonus_type) {
    case 'steal':
      return `${bonus.username} a volé des points au leader`;
    case 'shield':
      return `${bonus.username} s'est protégé contre le vol`;
    case 'time_bonus':
      return `${bonus.username} a ajouté 15s au timer`;
    case 'fog':
      return `${bonus.username} a brouillé les options des adversaires`;
    case 'fifty_fifty':
      return `${bonus.username} a retiré 2 mauvaises réponses`;
    case 'double_points':
      return `${bonus.username} a doublé ses points`;
    case 'max_points':
      return `${bonus.username} a obtenu le score maximum`;
    case 'joker':
      return `${bonus.username} a utilisé un joker`;
    default:
      return `${bonus.username} a utilisé ${meta.label}`;
  }
}

export default function RoundResultsScreen({
  round,
  players,
  correctAnswer,
  myPointsEarned,
  myAnswer,
  playerScores,
  roundBonuses,
  onContinue,
}: RoundResultsScreenProps) {
  const audio = useAudioPlayerOnResults(round, true);

  // Sort players by score and take top 5
  const topPlayers = [...players]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  // Find fastest correct player
  const fastestPlayer = playerScores
    ? Object.entries(playerScores)
        .filter(([, s]) => s.is_correct)
        .sort(([, a], [, b]) => a.response_time - b.response_time)[0]
    : null;

  // Extract year from extra_data if available
  const year = round.extra_data?.year || round.extra_data?.release_date?.substring(0, 4) || null;
  const albumImage = round.extra_data?.album_image;

  return (
    <div className="h-screen overflow-hidden bg-dark p-3 md:p-4 flex flex-col">
      <div className="flex-1 min-h-0 container mx-auto max-w-7xl flex flex-col">
        {/* Compact Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-500 rounded-t-2xl px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div>
              <h2 className="text-xl font-bold text-white">
                Fin du Round {round.round_number}
              </h2>
              <p className="text-white/90 text-sm">
                {myPointsEarned > 0 ? `+${myPointsEarned} points !` : 'Aucun point ce round'}
              </p>
            </div>
          </div>
          {/* Compact Audio Player */}
          <div className="flex items-center gap-2">
            {audio.isPlaying ? (
              <span className="text-white text-2xl animate-pulse">🎵</span>
            ) : audio.needsPlay ? (
              <button
                onClick={audio.handlePlay}
                className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition font-bold text-sm"
              >
                ▶️ Écouter
              </button>
            ) : (
              <span className="text-white text-2xl">⏳</span>
            )}
          </div>
        </div>

        {/* Main Content — 3 columns */}
        <div className="bg-white rounded-b-2xl shadow-2xl flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-0 overflow-hidden">

          {/* Left Column: Track Info (compact) */}
          <div className="lg:col-span-4 p-4 flex flex-col gap-3 overflow-y-auto min-h-0 border-r border-gray-100">
            {/* Album Art + Track Details side by side on desktop */}
            <div className="flex gap-3">
              {albumImage ? (
                <img
                  src={albumImage}
                  alt={`${round.track_name} album art`}
                  className="w-28 h-28 rounded-lg object-cover shadow-md shrink-0"
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              ) : (
                <div className="w-28 h-28 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 shadow-md flex items-center justify-center shrink-0">
                  <span className="text-white text-4xl">🎶</span>
                </div>
              )}
              <div className="flex flex-col justify-center min-w-0">
                <p className="text-lg font-bold text-gray-900 truncate">{round.track_name}</p>
                <p className="text-sm text-gray-600 truncate">{round.artist_name}</p>
                {year && <p className="text-xs text-gray-400">{year}</p>}
              </div>
            </div>

            {/* Answer section */}
            <div className="bg-gray-50 rounded-lg p-3 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-medium">Bonne réponse</span>
                <span className="text-sm font-bold text-green-600 truncate">{correctAnswer}</span>
              </div>
              {myAnswer !== undefined && myAnswer !== null && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">Votre réponse</span>
                  <span className={`text-sm font-bold truncate ${
                    myPointsEarned > 0 ? 'text-green-600' : 'text-red-500'
                  }`}>
                    {formatAnswer(myAnswer)} {myPointsEarned > 0 ? '✓' : '✗'}
                  </span>
                </div>
              )}
            </div>

            {/* Fastest Player Badge */}
            {fastestPlayer && (
              <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-3 flex items-center gap-3">
                <span className="text-2xl">⚡</span>
                <div className="min-w-0">
                  <p className="text-xs text-amber-600 font-semibold uppercase tracking-wide">Le plus rapide</p>
                  <p className="text-sm font-bold text-gray-900 truncate">{fastestPlayer[0]}</p>
                  <p className="text-xs text-amber-500">{fastestPlayer[1].response_time.toFixed(1)}s</p>
                </div>
              </div>
            )}

            {/* Bonus Section */}
            {roundBonuses && roundBonuses.length > 0 && (
              <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
                <p className="text-xs text-primary-600 font-semibold uppercase tracking-wide mb-2">
                  ⚡ Bonus utilisés
                </p>
                <div className="space-y-1.5">
                  {roundBonuses.map((bonus, i) => {
                    const meta = BONUS_META[bonus.bonus_type as BonusType];
                    return (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="text-base shrink-0">{meta?.emoji || '🎁'}</span>
                        <span className="text-gray-700">{describeBonusImpact(bonus)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Top 5 Players */}
          <div className="lg:col-span-8 p-4 flex flex-col min-h-0">
            <h3 className="text-lg font-bold text-gray-800 mb-3 shrink-0 flex items-center gap-2">
              <span>🏆</span> Classement
            </h3>

            <div className="space-y-2 flex-1 min-h-0 overflow-y-auto">
              {topPlayers.map((player, index) => (
                <div
                  key={player.id}
                  className={`flex items-center gap-3 rounded-xl p-3 transition-all ${
                    index === 0
                      ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 shadow-lg'
                      : index === 1
                      ? 'bg-gradient-to-r from-gray-200 to-gray-300 shadow'
                      : index === 2
                      ? 'bg-gradient-to-r from-orange-300 to-orange-400 shadow'
                      : 'bg-gray-50'
                  }`}
                >
                  {/* Medal / Rank */}
                  <div className="text-xl w-8 text-center shrink-0">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
                  </div>

                  {/* Avatar */}
                  <Avatar username={player.username} src={player.avatar} size="sm" className="shrink-0" />

                  {/* Player Info */}
                  <div className="flex-1 min-w-0">
                    <p className={`font-bold text-sm truncate ${index < 3 ? 'text-white' : 'text-gray-900'}`}>
                      {player.username}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs ${index < 3 ? 'text-white/80' : 'text-gray-500'}`}>
                        {player.score} pts
                      </span>
                      {playerScores?.[player.username] && (
                        <>
                          <span className={`text-xs ${
                            playerScores[player.username].is_correct
                              ? (index < 3 ? 'text-green-200' : 'text-green-500')
                              : (index < 3 ? 'text-red-200' : 'text-red-400')
                          }`}>
                            {playerScores[player.username].is_correct ? '✓' : '✗'}
                            {' '}+{playerScores[player.username].points_earned}
                          </span>
                          <span className={`text-xs ${index < 3 ? 'text-white/60' : 'text-gray-400'}`}>
                            ⏱ {playerScores[player.username].response_time.toFixed(1)}s
                          </span>
                          {(playerScores[player.username].streak_bonus ?? 0) > 0 && (
                            <span className={`text-xs ${index < 3 ? 'text-orange-200' : 'text-orange-400'}`}>
                              🔥×{playerScores[player.username].consecutive_correct}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Continue Button */}
            {onContinue && (
              <button
                onClick={onContinue}
                className="w-full mt-3 bg-primary-600 text-white font-bold py-4 px-6 rounded-xl hover:bg-primary-700 transition-all shadow-lg text-lg"
              >
                Continuer
              </button>
            )}
          </div>
        </div>

        {/* Auto-continue message */}
        <p className="text-center text-white/60 mt-2 text-xs shrink-0">
          Le prochain round commencera automatiquement...
        </p>
      </div>
    </div>
  );
}
