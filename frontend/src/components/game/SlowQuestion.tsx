import React from 'react';
import GenericQuestion from './GenericQuestion';
import type { Props } from './shared';

/**
 * SlowQuestion – Mode "Mollo" : la musique joue à 0.3× de sa vitesse normale.
 * Le joueur doit reconnaître le morceau malgré le tempo ralenti.
 */
const SlowQuestion = (props: Props) => (
  <GenericQuestion
    icon="🦥"
    defaultTitle="Quel est le titre de ce morceau ?"
    subtitle="La musique joue au ralenti — saurez-vous la reconnaître ?"
    audioLabel="Écoutez attentivement... (ralenti)"
    playbackRate={0.3}
    {...props}
  />
);

export default React.memo(SlowQuestion);
