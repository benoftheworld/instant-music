import React from 'react';
import GenericQuestion from './GenericQuestion';
import type { Props } from './shared';

/**
 * GuessArtistQuestion – Player hears audio and must identify the artist.
 */
const GuessArtistQuestion = (props: Props) => (
  <GenericQuestion
    icon="🎤"
    defaultTitle="Qui interprète ce morceau ?"
    audioLabel="Écoutez et trouvez l'artiste..."
    {...props}
  />
);

export default React.memo(GuessArtistQuestion);
