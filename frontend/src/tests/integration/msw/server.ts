/**
 * MSW Server — regroupe tous les handlers pour les tests d'intégration.
 */
import { setupServer } from 'msw/node';
import { authHandlers } from './handlers/authHandlers';
import { userHandlers } from './handlers/userHandlers';
import { gameHandlers } from './handlers/gameHandlers';
import { statsHandlers } from './handlers/statsHandlers';
import { achievementHandlers } from './handlers/achievementHandlers';
import { adminHandlers } from './handlers/adminHandlers';
import { socialHandlers } from './handlers/socialHandlers';
import { shopHandlers } from './handlers/shopHandlers';
import { youtubeHandlers } from './handlers/youtubeHandlers';
import { invitationHandlers } from './handlers/invitationHandlers';

export const server = setupServer(
  ...authHandlers,
  ...userHandlers,
  ...gameHandlers,
  ...statsHandlers,
  ...achievementHandlers,
  ...adminHandlers,
  ...socialHandlers,
  ...shopHandlers,
  ...youtubeHandlers,
  ...invitationHandlers,
);
