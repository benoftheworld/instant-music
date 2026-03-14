"""Tests unitaires de _build_leaderboard_entry."""

from unittest.mock import MagicMock, PropertyMock

from tests.base import BaseUnitTest


class TestBuildLeaderboardEntry(BaseUnitTest):
    """Vérifie la construction d'une entrée de leaderboard."""

    def get_target_class(self):
        from apps.stats.services import _build_leaderboard_entry
        return type(_build_leaderboard_entry)

    def _make_user(self, username="alice", has_team=True, has_avatar=True):
        user = MagicMock()
        user.id = "uid-1"
        user.username = username
        user.total_points = 500
        user.total_games_played = 10
        user.total_wins = 5
        user.win_rate = 50.0
        if has_avatar:
            user.avatar.url = "/media/alice.png"
        else:
            user.avatar = None
        if has_team:
            tm = MagicMock()
            tm.team.name = "TeamA"
            tm.team.id = "tid-1"
            user.team_memberships.first.return_value = tm
        else:
            user.team_memberships.first.return_value = None
        return user

    def test_basic_entry(self):
        from apps.stats.services import _build_leaderboard_entry
        user = self._make_user()
        entry = _build_leaderboard_entry(1, user)
        assert entry["rank"] == 1
        assert entry["username"] == "alice"
        assert entry["team_name"] == "TeamA"
        assert entry["total_points"] == 500

    def test_no_team(self):
        from apps.stats.services import _build_leaderboard_entry
        user = self._make_user(has_team=False)
        entry = _build_leaderboard_entry(1, user)
        assert entry["team_name"] is None
        assert entry["team_id"] is None

    def test_extra_fields_merged(self):
        from apps.stats.services import _build_leaderboard_entry
        user = self._make_user()
        entry = _build_leaderboard_entry(1, user, extra={"special": True})
        assert entry["special"] is True

    def test_no_avatar(self):
        from apps.stats.services import _build_leaderboard_entry
        user = self._make_user(has_avatar=False)
        entry = _build_leaderboard_entry(1, user)
        assert entry["avatar"] is None
