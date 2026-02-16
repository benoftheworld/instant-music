/**
 * Game mode icons and labels
 */
import type { GameMode } from '@/types';

export const GAME_MODE_CONFIG: Record<GameMode, { label: string; icon: string; description: string }> = {
  quiz_4: {
    label: 'Quiz Classique',
    icon: '🎵',
    description: 'Trouvez le bon titre parmi 4 propositions',
  },
  blind_test_inverse: {
    label: 'Trouver le Titre',
    icon: '🎯',
    description: 'Devinez le titre à partir de la musique',
  },
  guess_year: {
    label: 'Année',
    icon: '📅',
    description: 'Devinez l\'année de sortie du morceau',
  },
  guess_artist: {
    label: 'Artiste',
    icon: '🎤',
    description: 'Devinez l\'artiste du morceau',
  },
  intro: {
    label: 'Intro',
    icon: '⚡',
    description: 'Reconnaissez le morceau dès l\'intro',
  },
  lyrics: {
    label: 'Lyrics',
    icon: '📝',
    description: 'Complétez les paroles de la chanson',
  },
};

export const LEADERBOARD_TABS: { value: GameMode | 'general' | 'teams'; label: string; icon: string }[] = [
  { value: 'general', label: 'Général', icon: '🏆' },
  { value: 'teams', label: 'Équipes', icon: '👥' },
  { value: 'quiz_4', label: 'Quiz Classique', icon: '🎵' },
  { value: 'blind_test_inverse', label: 'Trouver le Titre', icon: '🎯' },
  { value: 'guess_year', label: 'Année', icon: '📅' },
  { value: 'guess_artist', label: 'Artiste', icon: '🎤' },
  { value: 'intro', label: 'Intro', icon: '⚡' },
  { value: 'lyrics', label: 'Lyrics', icon: '📝' },
];

/**
 * Get icon for a game mode
 */
export const getModeIcon = (mode: string): string => {
  return GAME_MODE_CONFIG[mode as GameMode]?.icon || '🎮';
};

/**
 * Get label for a game mode
 */
export const getModeLabel = (mode: string): string => {
  return GAME_MODE_CONFIG[mode as GameMode]?.label || mode;
};
