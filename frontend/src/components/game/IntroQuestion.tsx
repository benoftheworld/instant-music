import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
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
        <p className="text-gray-600">
          Artiste : <span className="font-semibold">{round.artist_name}</span>
        </p>
      </div>

      {!showResults && (
        <div className="mb-6">
          <AudioPlayerUI {...audio} label={`Intro — ${audioDuration}s seulement !`} />
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
