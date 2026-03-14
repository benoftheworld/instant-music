"""Tests unitaires de KaraokeSongSerializer.get_duration_display."""

from unittest.mock import MagicMock

from tests.base import BaseUnitTest


class TestKaraokeSongSerializerDuration(BaseUnitTest):
    """Vérifie le formatage mm:ss de la durée."""

    def get_target_class(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        return KaraokeSongSerializer

    def test_no_duration(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        ser = KaraokeSongSerializer()
        obj = MagicMock(duration_ms=None)
        assert ser.get_duration_display(obj) == "--:--"

    def test_zero_duration(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        ser = KaraokeSongSerializer()
        obj = MagicMock(duration_ms=0)
        assert ser.get_duration_display(obj) == "--:--"

    def test_exact_minutes(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        ser = KaraokeSongSerializer()
        obj = MagicMock(duration_ms=120000)
        assert ser.get_duration_display(obj) == "2:00"

    def test_minutes_and_seconds(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        ser = KaraokeSongSerializer()
        obj = MagicMock(duration_ms=185000)
        assert ser.get_duration_display(obj) == "3:05"

    def test_seconds_only(self):
        from apps.games.serializers.karaoke_song_serializer import KaraokeSongSerializer
        ser = KaraokeSongSerializer()
        obj = MagicMock(duration_ms=45000)
        assert ser.get_duration_display(obj) == "0:45"
