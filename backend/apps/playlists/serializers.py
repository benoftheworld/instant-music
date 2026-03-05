"""Serializers for playlists app.
"""

from rest_framework import serializers


class PlaylistSerializer(serializers.Serializer):
    """Lightweight serializer for Deezer playlists."""

    playlist_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    image_url = serializers.URLField(allow_blank=True)
    total_tracks = serializers.IntegerField(required=False, default=0)
    owner = serializers.CharField()
    external_url = serializers.URLField()
