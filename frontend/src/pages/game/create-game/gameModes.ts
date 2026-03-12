import type { GameMode, AnswerMode, GuessTarget } from '../../../types';

export const gameModes: { value: GameMode; label: string; description: string; icon: string }[] = [
  {
    value: 'classique',
    label: 'Classique',
    description: "La musique se lance au début du round. Trouvez l'artiste ou le titre.",
    icon: '🎵',
  },
  {
    value: 'rapide',
    label: 'Rapide',
    description: "3 secondes de musique puis silence. Trouvez l'artiste ou le titre.",
    icon: '⚡',
  },
  {
    value: 'generation',
    label: 'Génération',
    description: "Devinez l'année de sortie du morceau. Points selon la précision.",
    icon: '📅',
  },
  {
    value: 'paroles',
    label: 'Paroles',
    description: 'Complétez les paroles manquantes. Aucune musique pendant le round.',
    icon: '📝',
  },
  {
    value: 'karaoke',
    label: 'Karaoké',
    description: 'Mode solo : la musique complète joue via YouTube et les paroles défilent en rythme.',
    icon: '🎤',
  },
  {
    value: 'mollo',
    label: 'Mollo',
    description: 'La musique joue au ralenti (0.6×). Reconnaissez le morceau malgré le tempo changé.',
    icon: '🦥',
  },
];

export type { GameMode, AnswerMode, GuessTarget };
