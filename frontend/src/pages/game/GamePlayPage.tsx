import { useEffect, useReducer, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../store/authStore';
import {
  gamePlayReducer,
  initialGamePlayState,
} from '../../hooks/useGamePlayReducer';
import { useGameTimer } from '../../hooks/useGameTimer';
import { useGameWebSocket } from '../../hooks/useGameWebSocket';
import QuizQuestion from '../../components/game/QuizQuestion';
// BlindTestInverse removed - modes consolidated into classique/rapide/generation/paroles
import YearQuestion from '../../components/game/YearQuestion';
import IntroQuestion from '../../components/game/IntroQuestion';
import LyricsQuestion from '../../components/game/LyricsQuestion';
import KaraokeQuestion from '../../components/game/KaraokeQuestion';
import GuessArtistQuestion from '../../components/game/GuessArtistQuestion';
import SlowQuestion from '../../components/game/SlowQuestion';
import ReversedQuestion from '../../components/game/ReversedQuestion';
import TextModeQuestion from '../../components/game/TextModeQuestion';
import VolumeControl from '../../components/game/VolumeControl';
import LiveScoreboard from '../../components/game/LiveScoreboard';
import RoundLoadingScreen from '../../components/game/RoundLoadingScreen';
import RoundResultsScreen from '../../components/game/RoundResultsScreen';
import BonusActivator from '../../components/game/BonusActivator';

export default function GamePlayPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  // ── State (single reducer instead of 11 useState) ──────────────────────
  const [state, dispatch] = useReducer(gamePlayReducer, initialGamePlayState);
  const {
    game,
    currentRound,
    timeRemaining,
    hasAnswered,
    selectedAnswer,
    showResults,
    roundResults,
    loading,
    myPointsEarned,
    excludedOptions,
    roundPhase,
    fogActive,
    fogActivator,
  } = state;

  // ── Refs (imperative / timing concerns) ────────────────────────────────
  const isAdvancingRef = useRef(false);
  // Ref pour le timeout de passage au round suivant — permet de l'annuler si
  // round_ended est reçu deux fois (race condition) ou si le composant se démonte.
  const advanceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Timestamp (ms) captured the moment the round enters the 'playing' phase.
  // Used for an accurate response-time calculation that is immune to timer
  // drift, Math.floor rounding, and loading-screen offset mismatches.
  const roundPlayingStartTimeRef = useRef<number>(0);

  // ── WebSocket connection ───────────────────────────────────────────────
  const { sendMessage, onMessage } = useWebSocket(roomCode || '');

  // ── Data loading ───────────────────────────────────────────────────────

  const loadCurrentRound = useCallback(async () => {
    if (!roomCode) return;

    try {
      const response = await gameService.getCurrentRound(roomCode);

      if (response.current_round) {
        dispatch({ type: 'START_ROUND', round: response.current_round });
        roundPlayingStartTimeRef.current = 0;
      } else if (response.message === 'Partie terminée') {
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load round:', error);
    } finally {
      dispatch({ type: 'LOADING_DONE' });
    }
  }, [roomCode, navigate]);

  const loadGame = useCallback(async () => {
    if (!roomCode) return;

    try {
      const gameData = await gameService.getGame(roomCode);
      dispatch({ type: 'SET_GAME', game: gameData });

      if (gameData.status === 'finished') {
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load game:', error);
    }
  }, [roomCode, navigate]);

  // Advance to next round (guarded against double calls)
  const advanceToNextRound = useCallback(async () => {
    if (isAdvancingRef.current || !roomCode) return;
    isAdvancingRef.current = true;
    if (advanceTimeoutRef.current) {
      clearTimeout(advanceTimeoutRef.current);
      advanceTimeoutRef.current = null;
    }
    try {
      await gameService.nextRound(roomCode);
    } catch (error) {
      console.error('Failed to advance to next round:', error);
    } finally {
      // Reset after a delay to prevent rapid re-triggers
      setTimeout(() => { isAdvancingRef.current = false; }, 3000);
    }
  }, [roomCode]);

  // ── Extracted hooks ────────────────────────────────────────────────────

  useGameTimer({
    currentRound,
    showResults,
    roundPhase,
    game,
    roomCode,
    user,
    roundPlayingStartTimeRef,
    dispatch,
  });

  useGameWebSocket({
    onMessage,
    dispatch,
    game,
    user,
    roomCode,
    navigate,
    advanceToNextRound,
    advanceTimeoutRef,
    isAdvancingRef,
    roundPlayingStartTimeRef,
  });

  // Annuler le timeout de passage au round suivant si le composant se démonte
  // (navigation, fermeture de la page) avant qu'il se déclenche.
  useEffect(() => {
    return () => {
      if (advanceTimeoutRef.current) {
        clearTimeout(advanceTimeoutRef.current);
        advanceTimeoutRef.current = null;
      }
    };
  }, []);

  // Initial load
  useEffect(() => {
    loadGame();
    loadCurrentRound();
  }, [loadGame, loadCurrentRound]);

  // ── Handlers ───────────────────────────────────────────────────────────

  const handleAnswerSubmit = async (answer: string) => {
    if (!roomCode || !currentRound || hasAnswered) return;
    // Karaoke mode has no answers to submit
    if (game?.mode === 'karaoke') return;

    soundEffects.answerSubmitted();
    dispatch({ type: 'SUBMIT_ANSWER', answer });

    // Measure directly from when the playing phase started — avoids any drift
    // caused by Math.floor in the visual timer or loading-screen offset skew.
    const responseTime = roundPlayingStartTimeRef.current > 0
      ? Math.max(0, (Date.now() - roundPlayingStartTimeRef.current) / 1000)
      : Math.max(0, currentRound.duration - timeRemaining); // fallback if ref wasn't set

    try {
      // Submit answer to backend — response contains points_earned
      const answerResult = await gameService.submitAnswer(roomCode, {
        answer,
        response_time: responseTime
      });

      // Store the player's own points for immediate display
      dispatch({ type: 'SET_POINTS_EARNED', points: answerResult.points_earned || 0 });

      // Notify other players via WebSocket
      sendMessage({
        type: 'player_answer',
        player: user?.username || 'You',
        answer: answer,
        response_time: responseTime
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  // Callback when loading screen completes
  const handleLoadingComplete = () => {
    soundEffects.countdownGo();
    roundPlayingStartTimeRef.current = Date.now(); // ← start the response-time clock
    dispatch({ type: 'ENTER_PLAYING' });
    // Brouillard : démarrer le timer 5s maintenant que les options sont visibles
    if (fogActive) {
      setTimeout(() => dispatch({ type: 'SET_FOG', active: false, activator: null }), 5000);
    }
  };

  // ─── Render the correct question component based on game mode ───
  const renderQuestionComponent = () => {
    if (!currentRound) return null;

    const isTextMode = game?.answer_mode === 'text';
    const seekOffsetMs = (game?.timer_start_round || 5) * 1000;
    const mode = currentRound.extra_data?.round_mode || game?.mode;

    const commonProps = {
      round: currentRound,
      onAnswerSubmit: handleAnswerSubmit,
      hasAnswered,
      selectedAnswer,
      showResults,
      roundResults,
      seekOffsetMs, // Offset for the loading screen
      excludedOptions,
      fogBlur: fogActive && fogActivator !== user?.username,
    };

    // In text mode, we render the appropriate question component
    // but also overlay/replace the options with a text input.
    // For year mode, it already has a text input, so no change needed.
    // For other modes in text mode, we strip their OptionsGrid and add TextAnswerInput.

    if (isTextMode && mode !== 'generation' && mode !== 'karaoke') {
      // Text mode: use dedicated component that includes audio player
      return (
        <TextModeQuestion
          {...commonProps}
          placeholder={getTextPlaceholder()}
        />
      );
    }

    switch (mode) {
      case 'classique':
        // In MCQ mode, guess_target determines which component to render
        if (game?.guess_target === 'artist') {
          return <GuessArtistQuestion {...commonProps} />;
        }
        return <QuizQuestion {...commonProps} />;
      case 'rapide':
        return <IntroQuestion {...commonProps} />;
      case 'generation':
        return <YearQuestion {...commonProps} />;
      case 'paroles':
        return <LyricsQuestion {...commonProps} />;
      case 'karaoke': {
        // End the round when the YouTube video finishes (host only).
        // Non-hosts will receive the round_ended WebSocket message.
        const handleKaraokeEnded = () => {
          if (user && game && game.host === user.id && !showResults) {
            gameService.endCurrentRound(roomCode!)
              .catch(err => console.error('Failed to end karaoke round:', err));
          }
        };
        return <KaraokeQuestion {...commonProps} onSkipSong={handleKaraokeEnded} />;
      }
      case 'mollo':
        return <SlowQuestion {...commonProps} />;
      case 'inverse':
        return <ReversedQuestion {...commonProps} />;
      default:
        return <QuizQuestion {...commonProps} />;
    }
  };

  // ─── Helper for text mode placeholder ───
  const getTextPlaceholder = () => {
    switch (currentRound?.question_type) {
      case 'guess_artist': return 'Nom de l\'artiste...';
      case 'blind_inverse': return 'Titre du morceau...';
      case 'lyrics': return 'Le mot manquant...';
      default: return 'Titre du morceau...';
    }
  };

  // ─── Mode display name for header ───
  const getModeLabel = () => {
    switch (game?.mode) {
      case 'classique': return '🎵 Classique';
      case 'rapide': return '⚡ Rapide';
      case 'generation': return '📅 Génération';
      case 'paroles': return '📝 Paroles';
      case 'karaoke': return '🎤 Karaoké';
      default: return '🎵 Classique';
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Chargement...</div>
      </div>
    );
  }

  if (!currentRound) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">En attente du prochain round...</div>
      </div>
    );
  }

  // Show loading screen before round starts
  if (roundPhase === 'loading') {
    return (
      <RoundLoadingScreen
        roundNumber={currentRound.round_number}
        onComplete={handleLoadingComplete}
        duration={game?.timer_start_round || 5}
      />
    );
  }

  // Show results screen after round ends
  if (roundPhase === 'results' && roundResults) {
    return (
      <RoundResultsScreen
        round={currentRound}
        players={game?.players || []}
        correctAnswer={roundResults.correct_answer || currentRound.correct_answer || ''}
        myPointsEarned={myPointsEarned}
        myAnswer={selectedAnswer}
        playerScores={roundResults.player_scores}
      />
    );
  }

  // Show game screen during round
  const isKaraoke = game?.mode === 'karaoke';

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      {/* Live region pour annoncer les transitions de jeu aux lecteurs d'écran */}
      <div aria-live="polite" className="sr-only">
        {roundPhase === 'playing' && currentRound &&
          `Manche ${currentRound.round_number} — ${getModeLabel()} — ${timeRemaining} secondes`}
        {roundPhase === 'results' && roundResults &&
          `Résultats : la bonne réponse était ${roundResults.correct_answer}`}
      </div>

      <div className={`flex-1 flex flex-col min-h-0 container mx-auto ${isKaraoke ? 'max-w-7xl' : 'max-w-6xl'}`}>
        {/* Header with room code and round number */}
        <div className="flex justify-between items-center mb-3">
          <div className="text-white">
            <h1 className="text-2xl font-bold">Partie {roomCode}</h1>
            <div className="flex items-center gap-2">
              <p className="text-lg">
                {isKaraoke
                  ? getModeLabel()
                  : `Round ${currentRound.round_number} — ${getModeLabel()}`
                }
              </p>
              {game?.answer_mode === 'text' && !isKaraoke && (
                <span className="text-xs bg-amber-500/80 text-white px-2 py-0.5 rounded-full font-medium">
                  ⌨️ Saisie libre
                </span>
              )}
            </div>
          </div>

          {/* Timer — hidden for karaoke */}
          {!isKaraoke && (
            <div className="flex items-center gap-3">
              <VolumeControl variant="floating" />
              <div
                className={`text-6xl font-bold ${
                  timeRemaining <= 5 ? 'text-red-400 animate-pulse' : 'text-white'
                }`}
                role="timer"
                aria-label={`${timeRemaining} secondes restantes`}
              >
                {timeRemaining}s
              </div>
              {/* Annonces screen reader aux seuils critiques */}
              <div aria-live="assertive" className="sr-only">
                {timeRemaining === 10 && '10 secondes restantes'}
                {timeRemaining === 5 && '5 secondes restantes'}
              </div>
            </div>
          )}
          {isKaraoke && (
            <div className="flex items-center gap-3">
              <VolumeControl variant="floating" />
            </div>
          )}
        </div>

        {isKaraoke ? (
          /* Karaoke: full-width layout, no scoreboard */
          <div className="flex-1 min-h-0 overflow-y-auto">
            {renderQuestionComponent()}
          </div>
        ) : (
          <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main quiz area */}
            <div className="lg:col-span-2 overflow-y-auto min-h-0">
              {renderQuestionComponent()}
            </div>

            {/* Live scoreboard — hidden on mobile to free space for MCQ options */}
            <div className="hidden lg:block lg:col-span-1 overflow-y-auto min-h-0">
              <LiveScoreboard players={game?.players || []} />
            </div>
          </div>
        )}
      </div>
      {/* Panneau d'activation des bonus — flottant en bas à droite */}
      {roomCode && !isKaraoke && (
        <BonusActivator
          roomCode={roomCode}
          onBonusActivated={(_bonusType, extra) => {
            if (extra.excludedOptions && extra.excludedOptions.length > 0) {
              dispatch({ type: 'SET_EXCLUDED_OPTIONS', options: extra.excludedOptions });
            }
            // new_duration is handled via the bonus_activated WS event
          }}
        />
      )}
    </div>
  );
}
