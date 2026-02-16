import {
  useAudioPlayer, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * IntroQuestion – Same as classic quiz but audio stops after 5 seconds.
 * Player must recognize the track from just the intro.
 */
const IntroQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
}: Props) => {
  const audioDuration = round.extra_data?.audio_duration || 5;
  const audio = useAudioPlayer(round, showResults, audioDuration);

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Header with lightning bolt */}
      <div className="mb-6 text-center">
        <div className="inline-block bg-gradient-to-r from-yellow-400 to-red-500 text-white px-4 py-1 rounded-full text-sm font-bold mb-3 shadow">
          ⚡ {audioDuration} secondes d&apos;écoute
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          {round.question_text || 'Reconnaissez ce morceau !'}
        </h2>
      </div>

      {!showResults && (
        <div className="mb-6">
          <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg min-h-[120px]">
            {audio.playerError ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">⚠️</div>
                <p className="text-sm mb-1">{audio.playerError}</p>
              </div>
            ) : audio.isPlaying ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2 animate-pulse">🎵</div>
                <p className="text-sm">Intro — {audioDuration}s seulement !</p>
              </div>
            ) : (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">⏳</div>
                <p className="text-sm">Chargement de l&apos;intro...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {showResults && <TrackReveal round={round} />}

      <OptionsGrid
        options={round.options}
        hasAnswered={hasAnswered}
        showResults={showResults}
        selectedAnswer={selectedAnswer}
        roundResults={roundResults}
        onOptionClick={onAnswerSubmit}
      />

      <ResultFooter
        showResults={showResults}
        roundResults={roundResults}
        selectedAnswer={selectedAnswer}
        hasAnswered={hasAnswered}
      />
    </div>
  );
};

export default IntroQuestion;
