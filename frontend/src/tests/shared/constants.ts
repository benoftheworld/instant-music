/**
 * Constantes partagées entre tous les types de tests.
 */

/** URL de base de l'API (correspond à la config Vite) */
export const API_BASE_URL = 'http://localhost:8000';
export const API_URL = `${API_BASE_URL}/api`;

/** URL de base WebSocket */
export const WS_BASE_URL = 'ws://localhost:8000';

/** Regex de validation utilisées dans le frontend */
export const USERNAME_REGEX = /^[a-zA-Z0-9\-_']*$/;
export const EMAIL_REGEX = /^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$/;

/** Exemples de valeurs valides et invalides pour la regex username */
export const VALID_USERNAMES = ['alice', 'user-123', "l'artiste", 'A_B', 'a', 'Z', 'test123'];
export const INVALID_USERNAMES = ['alice bob', 'user@name', 'hello!', 'é', 'ñ', 'hello world', 'test<>'];

/** Exemples de valeurs valides et invalides pour la regex email */
export const VALID_EMAILS = ['a@b.co', 'user.name@domain.com', 'a-b_c@test.co.uk', 'test@example.org'];
export const INVALID_EMAILS = ['.user@d.com', 'user.@d.com', '@d.com', 'user@', 'plain-string', ''];

/** Password strength test cases */
export const PASSWORD_STRENGTH_CASES = [
  { password: '', expectedLabel: '' },
  { password: 'abc', expectedLabel: 'Faible' },
  { password: 'abcdefgh', expectedLabel: 'Faible' },
  { password: 'Abcdefgh', expectedLabel: 'Moyen' },
  { password: 'Abcdefgh1', expectedLabel: 'Moyen' },
  { password: 'Abcdefgh1!', expectedLabel: 'Fort' },
  { password: 'Abcdefghijkl1!', expectedLabel: 'Fort' },
];

/** Modes de jeu disponibles */
export const GAME_MODES = ['classique', 'rapide', 'generation', 'paroles', 'karaoke', 'mollo'] as const;

/** Statuts de jeu */
export const GAME_STATUSES = ['waiting', 'in_progress', 'finished', 'cancelled'] as const;
