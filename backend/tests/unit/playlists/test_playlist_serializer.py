"""Tests unitaires du PlaylistSerializer."""

from apps.playlists.serializers import PlaylistSerializer
from tests.base import BaseSerializerUnitTest


class TestPlaylistSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de playlist."""

    def get_serializer_class(self):
        return PlaylistSerializer

    def test_fields(self):
        serializer = PlaylistSerializer()
        expected = {
            "playlist_id", "name", "description", "image_url",
            "total_tracks", "owner", "external_url",
        }
        assert set(serializer.fields.keys()) == expected

    def test_total_tracks_default(self):
        serializer = PlaylistSerializer()
        assert serializer.fields["total_tracks"].default == 0

    def test_description_allow_blank(self):
        serializer = PlaylistSerializer()
        assert serializer.fields["description"].allow_blank is True

    def test_valid_data(self):
        data = {
            "playlist_id": "12345",
            "name": "Ma Playlist",
            "description": "",
            "image_url": "https://example.com/img.jpg",
            "total_tracks": 20,
            "owner": "deezer_user",
            "external_url": "https://example.com/playlist",
        }
        serializer = PlaylistSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_required_fields(self):
        serializer = PlaylistSerializer(data={})
        assert not serializer.is_valid()
        assert "playlist_id" in serializer.errors
        assert "name" in serializer.errors
