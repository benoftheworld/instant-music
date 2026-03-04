/**
 * Métadonnées partagées des bonus.
 *
 * Source unique de vérité pour les emojis, labels et couleurs des bonus,
 * utilisée par ShopPage, BonusActivator et tout composant affichant des bonus.
 */
import type { BonusType } from '@/types';

export interface BonusMeta {
  emoji: string;
  label: string;
  shortLabel: string;
  color: string;
  gradientClass: string;
  description: string;
}

export const BONUS_META: Record<BonusType, BonusMeta> = {
  double_points: {
    emoji: '✕2',
    label: 'Points Doublés',
    shortLabel: 'Points ×2',
    color: 'from-yellow-500 to-orange-500',
    gradientClass: 'bg-gradient-to-br from-yellow-500 to-orange-500',
    description: 'Double vos points sur le prochain round correct',
  },
  max_points: {
    emoji: '⭐',
    label: 'Points Maximum',
    shortLabel: 'Max pts',
    color: 'from-purple-500 to-pink-500',
    gradientClass: 'bg-gradient-to-br from-purple-500 to-pink-500',
    description: 'Obtenez 100 points (score maximum de base) peu importe votre temps de réponse',
  },
  time_bonus: {
    emoji: '⏱️',
    label: 'Temps Bonus',
    shortLabel: '+15 s',
    color: 'from-blue-500 to-cyan-500',
    gradientClass: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    description: '+15 secondes sur le timer du round en cours',
  },
  fifty_fifty: {
    emoji: '½',
    label: '50/50',
    shortLabel: '50/50',
    color: 'from-green-500 to-teal-500',
    gradientClass: 'bg-gradient-to-br from-green-500 to-teal-500',
    description: 'Retire 2 mauvaises réponses de vos choix (mode QCM uniquement)',
  },
  steal: {
    emoji: '🥷',
    label: 'Vol de Points',
    shortLabel: 'Vol',
    color: 'from-red-500 to-rose-600',
    gradientClass: 'bg-gradient-to-br from-red-500 to-rose-600',
    description: 'Vole 100 points au joueur en tête',
  },
  shield: {
    emoji: '🛡️',
    label: 'Bouclier',
    shortLabel: 'Bouclier',
    color: 'from-gray-400 to-slate-600',
    gradientClass: 'bg-gradient-to-br from-gray-400 to-slate-600',
    description: 'Protège vos points contre un vol',
  },
};

/** Raccourci pour récupérer les métadonnées d'un bonus. */
export const getBonusMeta = (type: BonusType): BonusMeta => BONUS_META[type];
