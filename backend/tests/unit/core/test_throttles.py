"""Tests unitaires des classes de throttle."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.core.throttles import (
    GameCreateThrottle,
    GameJoinThrottle,
    LeaderboardThrottle,
    LoginThrottle,
    PasswordResetThrottle,
    PlaylistSearchThrottle,
    RegisterThrottle,
    TokenRefreshThrottle,
)
from tests.base import BaseUnitTest


class TestThrottleClasses(BaseUnitTest):
    """Vérifie les scopes et types de chaque throttle."""

    def get_target_class(self):
        return RegisterThrottle

    def test_register_is_anon(self):
        assert issubclass(RegisterThrottle, AnonRateThrottle)

    def test_register_scope(self):
        assert RegisterThrottle.scope == "register"

    def test_login_is_anon(self):
        assert issubclass(LoginThrottle, AnonRateThrottle)

    def test_login_scope(self):
        assert LoginThrottle.scope == "login"

    def test_token_refresh_is_user(self):
        assert issubclass(TokenRefreshThrottle, UserRateThrottle)

    def test_token_refresh_scope(self):
        assert TokenRefreshThrottle.scope == "token_refresh"

    def test_game_create_is_user(self):
        assert issubclass(GameCreateThrottle, UserRateThrottle)

    def test_game_create_scope(self):
        assert GameCreateThrottle.scope == "game_create"

    def test_game_join_is_user(self):
        assert issubclass(GameJoinThrottle, UserRateThrottle)

    def test_game_join_scope(self):
        assert GameJoinThrottle.scope == "game_join"

    def test_playlist_search_is_user(self):
        assert issubclass(PlaylistSearchThrottle, UserRateThrottle)

    def test_playlist_search_scope(self):
        assert PlaylistSearchThrottle.scope == "playlist_search"

    def test_leaderboard_is_user(self):
        assert issubclass(LeaderboardThrottle, UserRateThrottle)

    def test_leaderboard_scope(self):
        assert LeaderboardThrottle.scope == "leaderboard"

    def test_password_reset_is_anon(self):
        assert issubclass(PasswordResetThrottle, AnonRateThrottle)

    def test_password_reset_scope(self):
        assert PasswordResetThrottle.scope == "password_reset"
