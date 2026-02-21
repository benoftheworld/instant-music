import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { getMediaUrl } from '../../services/api';

interface Player {
  id: string;
  username: string;
  score: number;
  rank: number;
  avatar?: string;
}

interface RoundAnswer {
  username: string;
  answer: string;
  is_correct: boolean;
  points_earned: number;
  response_time: number;
}

interface RoundDetail {
  round_number: number;
  track_name: string;
  artist_name: string;
  correct_answer: string;
  track_id: string;
  answers: RoundAnswer[];
}

interface GameResult {
  game: {
    id: string;
    room_code: string;
    status: string;
    mode: string;
    mode_display: string;
    answer_mode: string;
    answer_mode_display: string;
    guess_target: string;
    guess_target_display: string;
    num_rounds: number;
  };
  rankings: Player[];
  rounds: RoundDetail[];
}

export default function GameResultsPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<GameResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    const loadResults = async () => {
      if (!roomCode) return;

      try {
        const data = await gameService.getResults(roomCode);
        setResults(data);
      } catch (error) {
        console.error('Failed to load results:', error);
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [roomCode]);

  const getPodiumPosition = (rank: number) => {
    switch (rank) {
      case 1:
        return 'h-48 bg-gradient-to-b from-yellow-400 to-yellow-600';
      case 2:
        return 'h-40 bg-gradient-to-b from-gray-300 to-gray-500';
      case 3:
        return 'h-32 bg-gradient-to-b from-orange-400 to-orange-600';
      default:
        return 'h-24 bg-gradient-to-b from-blue-300 to-blue-500';
    }
  };

  const getMedal = (rank: number) => {
    switch (rank) {
      case 1:
        return '🥇';
      case 2:
        return '🥈';
      case 3:
        return '🥉';
      default:
        return `${rank}º`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Chargement des résultats...</div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Résultats introuvables</div>
      </div>
    );
  }

  const topThree = results.rankings.slice(0, 3);
  const others = results.rankings.slice(3);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="container mx-auto max-w-6xl py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">🎉 Partie Terminée ! 🎉</h1>
          <p className="text-xl text-white opacity-90">Partie {roomCode}</p>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-blue-500/80 text-white">
              {results.game.mode_display}
            </span>
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-purple-500/80 text-white">
              {results.game.answer_mode === 'mcq' ? '📋 QCM' : '⌨️ Saisie libre'}
            </span>
            {(results.game.mode === 'classique' || results.game.mode === 'rapide') && (
              <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-pink-500/80 text-white">
                {results.game.guess_target === 'artist' ? '🎤 Artiste' : '🎵 Titre'}
              </span>
            )}
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-gray-500/80 text-white">
              {results.game.num_rounds} rounds
            </span>
          </div>
        </div>

        {/* Podium */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-white text-center mb-8">🏆 Podium 🏆</h2>

          <div className="flex items-end justify-center space-x-4 mb-8">
            {/* 2nd place */}
            {topThree[1] && (
              <div className="flex flex-col items-center">
                <div className="text-4xl mb-2">🥈</div>
                {topThree[1].avatar ? (
                  <img
                    src={getMediaUrl(topThree[1].avatar)}
                    alt={topThree[1].username}
                    className="w-20 h-20 rounded-full mb-2 border-4 border-gray-400"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-white text-2xl font-bold mb-2 border-4 border-gray-400">
                    {topThree[1].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <p className="text-white font-bold text-lg mb-2">{topThree[1].username}</p>
                <div className={`w-32 ${getPodiumPosition(2)} rounded-t-lg flex flex-col items-center justify-center text-white`}>
                  <p className="text-3xl font-bold">{topThree[1].score}</p>
                  <p className="text-sm">points</p>
                </div>
              </div>
            )}

            {/* 1st place */}
            {topThree[0] && (
              <div className="flex flex-col items-center">
                <div className="text-5xl mb-2 animate-bounce">🥇</div>
                {topThree[0].avatar ? (
                  <img
                    src={getMediaUrl(topThree[0].avatar)}
                    alt={topThree[0].username}
                    className="w-24 h-24 rounded-full mb-2 border-4 border-yellow-400"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center text-white text-3xl font-bold mb-2 border-4 border-yellow-400">
                    {topThree[0].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <p className="text-white font-bold text-xl mb-2">{topThree[0].username}</p>
                <div className={`w-32 ${getPodiumPosition(1)} rounded-t-lg flex flex-col items-center justify-center text-white`}>
                  <p className="text-4xl font-bold">{topThree[0].score}</p>
                  <p className="text-sm">points</p>
                </div>
              </div>
            )}

            {/* 3rd place */}
            {topThree[2] && (
              <div className="flex flex-col items-center">
                <div className="text-4xl mb-2">🥉</div>
                {topThree[2].avatar ? (
                  <img
                    src={getMediaUrl(topThree[2].avatar)}
                    alt={topThree[2].username}
                    className="w-20 h-20 rounded-full mb-2 border-4 border-orange-400"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-2xl font-bold mb-2 border-4 border-orange-400">
                    {topThree[2].username.charAt(0).toUpperCase()}
                  </div>
                )}
                <p className="text-white font-bold text-lg mb-2">{topThree[2].username}</p>
                <div className={`w-32 ${getPodiumPosition(3)} rounded-t-lg flex flex-col items-center justify-center text-white`}>
                  <p className="text-3xl font-bold">{topThree[2].score}</p>
                  <p className="text-sm">points</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Other players */}
        {others.length > 0 && (
          <div className="max-w-2xl mx-auto mb-8">
            <h3 className="text-2xl font-bold text-white text-center mb-4">Autres joueurs</h3>
            <div className="space-y-2">
              {others.map((player) => (
                <div
                  key={player.id}
                  className="bg-white/10 backdrop-blur-sm rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl font-bold text-white">{getMedal(player.rank)}</span>
                    {player.avatar ? (
                      <img
                        src={getMediaUrl(player.avatar)}
                        alt={player.username}
                        className="w-12 h-12 rounded-full"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold">
                        {player.username.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className="text-white font-semibold text-lg">{player.username}</span>
                  </div>
                  <div className="text-white font-bold text-2xl">{player.score} pts</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Per-round recap */}
        {results.rounds && results.rounds.length > 0 && (
          <div className="max-w-4xl mx-auto mb-12">
            <h3 className="text-3xl font-bold text-white text-center mb-6">📋 Récapitulatif par round</h3>
            <div className="space-y-4">
              {results.rounds.map((round) => (
                <div
                  key={round.round_number}
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-5"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <span className="text-white font-bold text-lg">
                        Round {round.round_number}
                      </span>
                      <span className="text-white/70 ml-3">
                        🎵 {round.track_name} — {round.artist_name}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {round.answers.map((ans, idx) => (
                      <div
                        key={idx}
                        className={`rounded-lg px-4 py-2 flex items-center justify-between ${
                          ans.is_correct
                            ? 'bg-green-500/30 border border-green-400/50'
                            : 'bg-red-500/20 border border-red-400/30'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">{ans.is_correct ? '✅' : '❌'}</span>
                          <span className="text-white font-medium">{ans.username}</span>
                        </div>
                        <div className="text-right">
                          <span className={`font-bold ${ans.is_correct ? 'text-green-300' : 'text-red-300'}`}>
                            +{ans.points_earned}
                          </span>
                          <span className="text-white/50 text-xs ml-1">
                            ({ans.response_time}s)
                          </span>
                        </div>
                      </div>
                    ))}
                    {round.answers.length === 0 && (
                      <p className="text-white/50 text-sm col-span-full">Aucune réponse</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3 bg-white text-blue-600 rounded-lg font-bold hover:bg-gray-100 transition"
          >
            Retour à l'accueil
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
            className="px-8 py-3 bg-emerald-600 text-white rounded-lg font-bold hover:bg-emerald-700 transition disabled:opacity-50 flex items-center gap-2"
          >
            {downloadingPdf ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Génération…
              </>
            ) : (
              <>📄 Télécharger PDF</>
            )}
          </button>
          <button
            onClick={() => navigate('/game/create')}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition"
          >
            Nouvelle partie
          </button>
        </div>
      </div>
    </div>
  );
}
