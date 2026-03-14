"""Rate limiting throttle classes par endpoint."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class RegisterThrottle(AnonRateThrottle):
    """Throttle pour les inscriptions."""

    scope = "register"


class LoginThrottle(AnonRateThrottle):
    """Throttle pour la connexion."""

    scope = "login"


class TokenRefreshThrottle(UserRateThrottle):
    """Throttle pour le rafraîchissement de token."""

    scope = "token_refresh"


class GameCreateThrottle(UserRateThrottle):
    """Throttle pour la création de partie."""

    scope = "game_create"


class GameJoinThrottle(UserRateThrottle):
    """Throttle pour rejoindre une partie."""

    scope = "game_join"


class PlaylistSearchThrottle(UserRateThrottle):
    """Throttle pour la recherche de playlist."""

    scope = "playlist_search"


class LeaderboardThrottle(UserRateThrottle):
    """Throttle pour le classement."""

    scope = "leaderboard"


class PasswordResetThrottle(AnonRateThrottle):
    """Throttle pour la réinitialisation du mot de passe."""

    scope = "password_reset"
