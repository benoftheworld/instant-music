import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { soundEffects } from '../../services/soundEffects';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../store/authStore';
import QuizQuestion from '../../components/game/QuizQuestion';
// BlindTestInverse removed - modes consolidated into classique/rapide/generation/paroles
import YearQuestion from '../../components/game/YearQuestion';
import IntroQuestion from '../../components/game/IntroQuestion';
import LyricsQuestion from '../../components/game/LyricsQuestion';
import KaraokeQuestion from '../../components/game/KaraokeQuestion';
import GuessArtistQuestion from '../../components/game/GuessArtistQuestion';
import TextModeQuestion from '../../components/game/TextModeQuestion';
import VolumeControl from '../../components/game/VolumeControl';
import LiveScoreboard from '../../components/game/LiveScoreboard';
import RoundLoadingScreen from '../../components/game/RoundLoadingScreen';
import RoundResultsScreen from '../../components/game/RoundResultsScreen';

interface Round {
  id: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  preview_url?: string;
  options: string[];
  question_type: string;
  question_text: string;
  extra_data: Record<string, any>;
  duration: number;
  started_at: string;
  ended_at: string | null;
  correct_answer?: string;
}

export default function GamePlayPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const [game, setGame] = useState<any>(null);
  const [currentRound, setCurrentRound] = useState<Round | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [hasAnswered, setHasAnswered] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [roundResults, setRoundResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [myPointsEarned, setMyPointsEarned] = useState<number>(0);
  const isAdvancingRef = useRef(false);

  // New state for round phases: 'loading' | 'playing' | 'results'
  const [roundPhase, setRoundPhase] = useState<'loading' | 'playing' | 'results'>('loading');
  const loadingStartTimeRef = useRef<number>(0);

  // WebSocket connection
  const { sendMessage, onMessage } = useWebSocket(roomCode || '');

  // Load current round
  const loadCurrentRound = useCallback(async () => {
    if (!roomCode) return;

    try {
      const response = await gameService.getCurrentRound(roomCode);

      if (response.current_round) {
        setCurrentRound(response.current_round);
        setTimeRemaining(response.current_round.duration);
        setHasAnswered(false);
        setSelectedAnswer(null);
        setShowResults(false);
        setRoundPhase('loading'); // Start with loading phase
        loadingStartTimeRef.current = Date.now(); // Record when loading starts
      } else if (response.message === 'Partie terminée') {
        // Game is finished
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load round:', error);
    } finally {
      setLoading(false);
    }
  }, [roomCode, navigate]);

  // Load game data
  const loadGame = useCallback(async () => {
    if (!roomCode) return;

    try {
      const gameData = await gameService.getGame(roomCode);
      setGame(gameData);

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
    try {
      await gameService.nextRound(roomCode);
    } catch (error) {
      console.error('Failed to advance to next round:', error);
    } finally {
      // Reset after a delay to prevent rapid re-triggers
      setTimeout(() => { isAdvancingRef.current = false; }, 3000);
    }
  }, [roomCode]);

  // Timer countdown - calculate based on server time
  useEffect(() => {
    if (!currentRound || showResults || roundPhase !== 'playing') return;

    // Use game's timer_start_round for loading screen offset
    const loadingDurationMs = (game?.timer_start_round || 5) * 1000;

    const calculateTimeRemaining = () => {
      if (!currentRound.started_at) return currentRound.duration;
      const startTime = new Date(currentRound.started_at).getTime();
      const now = Date.now();

      // Compensate for the loading screen duration
      const adjustedStartTime = startTime + (loadingStartTimeRef.current > 0 ? loadingDurationMs : 0);

      const elapsed = Math.floor((now - adjustedStartTime) / 1000);
      const remaining = Math.max(0, currentRound.duration - elapsed);
      return remaining;
    };

    // Update immediately
    const remaining = calculateTimeRemaining();
    setTimeRemaining(remaining);
    let lastSecond = remaining;

    let timerTimeout: ReturnType<typeof setTimeout> | null = null;

    // Update every 100ms for smooth countdown
    const interval = setInterval(() => {
      const newRemaining = calculateTimeRemaining();
      setTimeRemaining(newRemaining);

      // Sound effects for countdown
      if (newRemaining !== lastSecond && newRemaining > 0) {
        if (newRemaining <= 3) {
          soundEffects.timerWarning();
        } else if (newRemaining <= 5) {
          soundEffects.timerTick();
        }
        lastSecond = newRemaining;
      }

      if (newRemaining <= 0) {
        clearInterval(interval);
        soundEffects.timeUp();

        // Host terminates the round immediately to send results to all players
        if (user && game && game.host === user.id) {
          // End the round (triggers round_ended broadcast with results)
          gameService.endCurrentRound(roomCode!)
            .then(() => {
              console.log('Round ended by timer');
            })
            .catch(err => {
              console.error('Failed to end round:', err);
              // Fallback: show local results if backend call fails
              setShowResults(true);
              setRoundPhase('results');
            });
        }
        // Non-hosts: wait for round_ended message from WebSocket
      }
    }, 100);

    return () => {
      clearInterval(interval);
      if (timerTimeout) clearTimeout(timerTimeout);
    };
  }, [currentRound, showResults, roundPhase, game, roomCode, user, advanceToNextRound]);

  // Handle WebSocket messages
  useEffect(() => {
    const unsubscribe = onMessage('message', (data: any) => {
      console.log('WebSocket message:', data);

      switch (data.type) {
        case 'round_started':
          // New round started
          soundEffects.roundLoading();
          setCurrentRound(data.round_data);
          setTimeRemaining(data.round_data.duration);
          setHasAnswered(false);
          setSelectedAnswer(null);
          setShowResults(false);
          setRoundPhase('loading'); // Show loading screen first
          loadingStartTimeRef.current = Date.now(); // Record when loading starts
          break;

        case 'player_answered':
          // Another player answered
          console.log('Player answered:', data.player);
          break;

        case 'round_ended': {
          // Round finished, show results
          const myScoreData = data.results?.player_scores?.[user?.username || ''];
          const wasCorrect = myScoreData?.is_correct;

          // Play appropriate sound (skip for karaoke — no answer to judge)
          if (game?.mode !== 'karaoke') {
            if (wasCorrect) {
              soundEffects.correctAnswer();
            } else {
              soundEffects.wrongAnswer();
            }
          }

          setShowResults(true);
          setRoundPhase('results'); // Show results screen
          setRoundResults({
            ...data.results,
            points_earned: myScoreData?.points_earned ?? myPointsEarned,
          });
          // Update players with fresh scores from backend (functional update to avoid stale closure)
          if (data.results?.updated_players) {
            setGame((prev: any) => prev ? { ...prev, players: data.results.updated_players } : prev);
          }

          // Host advances to next round after result display time
          // Karaoke: quick transition (2s); other modes: configurable
          const isKaraokeMode = game?.mode === 'karaoke';
          const resultDisplayTime = isKaraokeMode ? 2000 : (game?.score_display_duration || 10) * 1000;
          if (user && game && game.host === user.id) {
            setTimeout(() => {
              advanceToNextRound();
            }, resultDisplayTime);
          }
          break;
        }

        case 'next_round':
          // Move to next round automatically
          soundEffects.roundLoading();
          isAdvancingRef.current = false;
          setCurrentRound(data.round_data);
          setTimeRemaining(data.round_data.duration);
          setHasAnswered(false);
          setSelectedAnswer(null);
          setShowResults(false);
          setRoundResults(null);
          setMyPointsEarned(0);
          setRoundPhase('loading'); // Show loading screen for new round
          loadingStartTimeRef.current = Date.now(); // Record when loading starts
          // Update players with fresh scores (functional update to avoid stale closure)
          if (data.updated_players) {
            setGame((prev: any) => prev ? { ...prev, players: data.updated_players } : prev);
          }
          break;

        case 'game_finished':
          // Game over
          soundEffects.gameFinished();
          navigate(`/game/${roomCode}/results`);
          break;
      }
    });

    return unsubscribe;
  }, [onMessage, loadCurrentRound, navigate, roomCode, user, game, advanceToNextRound]);

  // Initial load
  useEffect(() => {
    loadGame();
    loadCurrentRound();
  }, [loadGame, loadCurrentRound]);

  // Handle answer submission
  const handleAnswerSubmit = async (answer: string) => {
    if (!roomCode || !currentRound || hasAnswered) return;
    // Karaoke mode has no answers to submit
    if (game?.mode === 'karaoke') return;

    soundEffects.answerSubmitted();
    setSelectedAnswer(answer);
    setHasAnswered(true);

    const responseTime = currentRound.duration - timeRemaining;

    try {
      // Submit answer to backend — response contains points_earned
      const answerResult = await gameService.submitAnswer(roomCode, {
        answer,
        response_time: responseTime
      });

      // Store the player's own points for immediate display
      setMyPointsEarned(answerResult.points_earned || 0);

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
  // ── Karaoke: skip to next song ──
  const handleKaraokeSkip = useCallback(async () => {
    if (!roomCode || isAdvancingRef.current) return;
    isAdvancingRef.current = true;
    try {
      // End current round, then advance
      await gameService.endCurrentRound(roomCode);
      // Small delay then advance
      setTimeout(async () => {
        try {
          await gameService.nextRound(roomCode);
        } catch { /* will come via WS */ }
        setTimeout(() => { isAdvancingRef.current = false; }, 2000);
      }, 500);
    } catch {
      isAdvancingRef.current = false;
    }
  }, [roomCode]);
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
      case 'karaoke':
        return <KaraokeQuestion {...commonProps} onSkipSong={handleKaraokeSkip} />;
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

  // Callback when loading screen completes
  const handleLoadingComplete = () => {
    soundEffects.countdownGo();
    setRoundPhase('playing');
  };

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
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className={`container mx-auto ${isKaraoke ? 'max-w-7xl' : 'max-w-6xl'}`}>
        {/* Header with room code and round number */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-white">
            <h1 className="text-2xl font-bold">Partie {roomCode}</h1>
            <div className="flex items-center gap-2">
              <p className="text-lg">
                {isKaraoke
                  ? `Chanson ${currentRound.round_number} — ${getModeLabel()}`
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
              <div className={`text-6xl font-bold ${
                timeRemaining <= 5 ? 'text-red-400 animate-pulse' : 'text-white'
              }`}>
                {timeRemaining}s
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
          <div>
            {renderQuestionComponent()}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main quiz area */}
            <div className="lg:col-span-2">
              {renderQuestionComponent()}
            </div>

            {/* Live scoreboard */}
            <div className="lg:col-span-1">
              <LiveScoreboard players={game?.players || []} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
