"""Rate limiting throttle classes par endpoint."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class TokenRefreshThrottle(UserRateThrottle):
    scope = "token_refresh"


class GameCreateThrottle(UserRateThrottle):
    scope = "game_create"


class GameJoinThrottle(UserRateThrottle):
    scope = "game_join"


class PlaylistSearchThrottle(UserRateThrottle):
    scope = "playlist_search"


class LeaderboardThrottle(UserRateThrottle):
    scope = "leaderboard"
