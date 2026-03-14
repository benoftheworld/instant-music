"""Tests unitaires de GameHistorySerializer."""

from unittest.mock import MagicMock, PropertyMock

from tests.base import BaseUnitTest


class TestGameHistorySerializer(BaseUnitTest):
    """Vérifie les méthodes SerializerMethodField de GameHistorySerializer."""

    def get_target_class(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        return GameHistorySerializer

    def _make_player(self, score, username="alice", has_avatar=True):
        user = MagicMock()
        user.username = username
        user.id = f"id-{username}"
        if has_avatar:
            user.avatar.url = f"/media/{username}.png"
        else:
            user.avatar = None
        p = MagicMock()
        p.score = score
        p.user = user
        return p

    def _make_game_obj(self, players):
        obj = MagicMock()
        obj.players.all.return_value = players
        return obj

    def test_sorted_players_descending(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        p1 = self._make_player(50, "bob")
        p2 = self._make_player(100, "alice")
        obj = self._make_game_obj([p1, p2])
        result = ser._sorted_players(obj)
        assert result[0].score == 100
        assert result[1].score == 50

    def test_get_winner_returns_top_player(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        p1 = self._make_player(100, "alice")
        obj = self._make_game_obj([p1])
        result = ser.get_winner(obj)
        assert result["username"] == "alice"

    def test_get_winner_no_players(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        obj = self._make_game_obj([])
        assert ser.get_winner(obj) is None

    def test_get_winner_score_empty(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        obj = self._make_game_obj([])
        assert ser.get_winner_score(obj) == 0

    def test_get_winner_score(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        p1 = self._make_player(200, "alice")
        obj = self._make_game_obj([p1])
        assert ser.get_winner_score(obj) == 200

    def test_get_player_count(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        obj = self._make_game_obj([self._make_player(10), self._make_player(20)])
        assert ser.get_player_count(obj) == 2

    def test_get_participants_ranked(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        p1 = self._make_player(100, "alice")
        p2 = self._make_player(50, "bob")
        obj = self._make_game_obj([p1, p2])
        result = ser.get_participants(obj)
        assert len(result) == 2
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2

    def test_get_winner_no_avatar(self):
        from apps.games.serializers.game_history_serializer import GameHistorySerializer
        ser = GameHistorySerializer()
        p1 = self._make_player(100, "alice", has_avatar=False)
        obj = self._make_game_obj([p1])
        result = ser.get_winner(obj)
        assert result["avatar"] is None
