import React from 'react';
import GenericQuestion from './GenericQuestion';
import type { Props } from './shared';

/**
 * QuizQuestion – Default classique mode (and fallback for unknown modes).
 * Plays audio, shows 4 options, player picks the correct title.
 */
const QuizQuestion = (props: Props) => (
  <GenericQuestion
    icon="🎵"
    defaultTitle="Quel est le titre de ce morceau ?"
    subtitle="L'artiste sera révélé à la fin du round"
    {...props}
  />
);

export default React.memo(QuizQuestion);
