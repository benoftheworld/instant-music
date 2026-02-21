"""
Serializers for playlists app (YouTube-backed).

Only the lightweight `YouTubePlaylistSerializer` is retained — DB-backed
`Playlist`/`Track` serializers were removed along with the models.
"""
from rest_framework import serializers


class YouTubePlaylistSerializer(serializers.Serializer):
    youtube_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    image_url = serializers.URLField(allow_blank=True)
    total_tracks = serializers.IntegerField(required=False, default=0)
    owner = serializers.CharField()
    external_url = serializers.URLField()
