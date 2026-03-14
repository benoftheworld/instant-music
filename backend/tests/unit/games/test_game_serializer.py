"""Tests unitaires de GameSerializer.get_player_count."""

from unittest.mock import MagicMock

from tests.base import BaseUnitTest


class TestGameSerializerPlayerCount(BaseUnitTest):
    """Vérifie les 3 chemins de get_player_count."""

    def get_target_class(self):
        from apps.games.serializers.game_serializer import GameSerializer
        return GameSerializer

    def test_annotation_path(self):
        from apps.games.serializers.game_serializer import GameSerializer
        ser = GameSerializer()
        obj = MagicMock()
        obj._player_count = 5
        assert ser.get_player_count(obj) == 5

    def test_prefetch_path(self):
        from apps.games.serializers.game_serializer import GameSerializer
        ser = GameSerializer()
        obj = MagicMock()
        # Remove _player_count so hasattr returns False
        del obj._player_count
        obj._prefetched_objects_cache = {"players": True}
        obj.players.all.return_value = [1, 2, 3]
        assert ser.get_player_count(obj) == 3

    def test_count_fallback(self):
        from apps.games.serializers.game_serializer import GameSerializer
        ser = GameSerializer()
        obj = MagicMock()
        del obj._player_count
        obj._prefetched_objects_cache = {}
        obj.players.count.return_value = 7
        assert ser.get_player_count(obj) == 7

    def test_no_prefetch_cache_attr(self):
        from apps.games.serializers.game_serializer import GameSerializer
        ser = GameSerializer()
        obj = MagicMock()
        del obj._player_count
        del obj._prefetched_objects_cache
        obj.players.count.return_value = 2
        assert ser.get_player_count(obj) == 2
