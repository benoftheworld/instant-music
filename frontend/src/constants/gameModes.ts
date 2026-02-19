/**
 * Game mode icons and labels
 */
import type { GameMode } from '@/types';

export const GAME_MODE_CONFIG: Record<GameMode, { label: string; icon: string; description: string }> = {
  classique: {
    label: 'Classique',
    icon: '🎵',
    description: 'La musique se lance, trouvez l\'artiste ou le titre',
  },
  rapide: {
    label: 'Rapide',
    icon: '⚡',
    description: '3 secondes de musique puis silence pour répondre',
  },
  generation: {
    label: 'Génération',
    icon: '📅',
    description: 'Devinez l\'année de sortie du morceau',
  },
  paroles: {
    label: 'Paroles',
    icon: '📝',
    description: 'Complétez les paroles manquantes de la chanson',
  },
  karaoke: {
    label: 'Karaoké',
    icon: '🎤',
    description: 'Les paroles défilent en rythme, devinez le titre !',
  },
};

export const LEADERBOARD_TABS: { value: GameMode | 'general' | 'teams'; label: string; icon: string }[] = [
  { value: 'general', label: 'Général', icon: '🏆' },
  { value: 'teams', label: 'Équipes', icon: '👥' },
  { value: 'classique', label: 'Classique', icon: '🎵' },
  { value: 'rapide', label: 'Rapide', icon: '⚡' },
  { value: 'generation', label: 'Génération', icon: '📅' },
  { value: 'paroles', label: 'Paroles', icon: '📝' },
  { value: 'karaoke', label: 'Karaoké', icon: '🎤' },
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
