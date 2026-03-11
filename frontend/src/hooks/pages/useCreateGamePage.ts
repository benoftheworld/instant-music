import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import type { GameMode, AnswerMode, GuessTarget, YouTubePlaylist, KaraokeSong, CreateGameData } from '../../types';

export function useCreateGamePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  // Step 1: Game mode
  const [selectedMode, setSelectedMode] = useState<GameMode>('classique');
  const [answerMode, setAnswerMode] = useState<AnswerMode>('mcq');
  const [guessTarget, setGuessTarget] = useState<GuessTarget>('title');
  const [lyricsWordsCount, setLyricsWordsCount] = useState(3);

  // Step 2: Global config (non-karaoke only)
  const [roundDuration, setRoundDuration] = useState(30);
  const [scoreDisplayDuration, setScoreDisplayDuration] = useState(10);
  const [maxPlayers, setMaxPlayers] = useState(8);
  const [numRounds, setNumRounds] = useState(10);
  const [isOnline, setIsOnline] = useState(true);
  const [isPublic, setIsPublic] = useState(false);
  const [isPartyMode, setIsPartyMode] = useState(false);
  const [isBonusesEnabled, setIsBonusesEnabled] = useState(true);

  // Step 3: Playlist (non-karaoke) or karaoke song
  const [selectedPlaylist, setSelectedPlaylist] = useState<YouTubePlaylist | null>(null);
  const [karaokeSelectedSong, setKaraokeSelectedSong] = useState<KaraokeSong | null>(null);

  const isKaraoke = selectedMode === 'karaoke';
  const LAST_STEP = 4;

  const nextStep = () => {
    if (currentStep === 1 && isKaraoke) {
      setCurrentStep(3);
    } else if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep === 3 && isKaraoke) {
      setCurrentStep(1);
    } else if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return true;
      case 2: return true;
      case 3: return isKaraoke ? !!karaokeSelectedSong : !!selectedPlaylist;
      default: return true;
    }
  };

  const handleCreateGame = async () => {
    if (isKaraoke) {
      if (!karaokeSelectedSong) {
        setError('Veuillez sélectionner un morceau dans le catalogue');
        setCurrentStep(3);
        return;
      }
    } else {
      if (!selectedPlaylist) {
        setError('Veuillez sélectionner une playlist');
        setCurrentStep(3);
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const gameData: CreateGameData = {
        mode: selectedMode,
        max_players: isKaraoke ? 1 : maxPlayers,
        num_rounds: isKaraoke ? 1 : numRounds,
        playlist_id: isKaraoke ? undefined : selectedPlaylist?.youtube_id,
        playlist_name: isKaraoke ? undefined : selectedPlaylist?.name,
        playlist_image_url: isKaraoke ? undefined : selectedPlaylist?.image_url,
        karaoke_song_id: isKaraoke ? karaokeSelectedSong!.id : undefined,
        is_online: isKaraoke ? false : isOnline,
        is_public: isKaraoke ? false : isPublic,
        is_party_mode: isKaraoke ? false : (isOnline ? isPartyMode : false),
        bonuses_enabled: isKaraoke ? false : (isOnline ? isBonusesEnabled : false),
        answer_mode: answerMode,
        guess_target: guessTarget,
        round_duration: roundDuration,
        score_display_duration: isKaraoke ? 0 : scoreDisplayDuration,
        lyrics_words_count: selectedMode === 'paroles' ? lyricsWordsCount : undefined,
      };

      const game = await gameService.createGame(gameData);
      navigate(`/game/lobby/${game.room_code}`);
    } catch (err) {
      console.error('Failed to create game:', err);
      const error = err as { response?: { data?: { error?: string; non_field_errors?: string[] } } };
      const msg = error.response?.data?.error
        || error.response?.data?.non_field_errors?.[0]
        || 'Erreur lors de la création de la partie';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMode = (mode: GameMode) => {
    setSelectedMode(mode);
    if (mode === 'karaoke') setMaxPlayers(1);
  };

  const handleToggleOffline = (checked: boolean) => {
    setIsOnline(!checked);
    if (checked) {
      setIsPublic(false);
      setMaxPlayers(1);
      setIsBonusesEnabled(false);
    } else {
      setMaxPlayers(8);
      setIsBonusesEnabled(true);
    }
  };

  const handleSelectPlaylist = (playlist: YouTubePlaylist | null) => {
    setSelectedPlaylist(playlist);
    setError(null);
  };

  const handleSelectKaraokeSong = (song: KaraokeSong | null) => {
    setKaraokeSelectedSong(song);
    setError(null);
  };

  return {
    navigate,
    loading,
    error,
    currentStep,
    setCurrentStep,
    selectedMode,
    answerMode,
    setAnswerMode,
    guessTarget,
    setGuessTarget,
    lyricsWordsCount,
    setLyricsWordsCount,
    roundDuration,
    setRoundDuration,
    scoreDisplayDuration,
    setScoreDisplayDuration,
    maxPlayers,
    setMaxPlayers,
    numRounds,
    setNumRounds,
    isOnline,
    isPublic,
    setIsPublic,
    isPartyMode,
    setIsPartyMode,
    isBonusesEnabled,
    setIsBonusesEnabled,
    selectedPlaylist,
    karaokeSelectedSong,
    isKaraoke,
    LAST_STEP,
    nextStep,
    prevStep,
    canProceed,
    handleCreateGame,
    handleSelectMode,
    handleToggleOffline,
    handleSelectPlaylist,
    handleSelectKaraokeSong,
  };
}
