"""
Serializers for playlists app (YouTube-backed).
"""
from rest_framework import serializers
from .models import Playlist, Track


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for Playlist model (cached data)."""
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'youtube_id', 'name', 'description',
            'image_url', 'total_tracks', 'owner', 'external_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrackSerializer(serializers.ModelSerializer):
    """Serializer for Track model (cached data)."""
    
    artists_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Track
        fields = [
            'id', 'youtube_id', 'name', 'artists', 'artists_display',
            'album', 'album_image', 'duration_ms', 'preview_url',
            'external_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_artists_display(self, obj) -> str:
        return ', '.join(obj.artists) if obj.artists else 'Unknown'


class YouTubePlaylistSerializer(serializers.Serializer):
    """Serializer for YouTube API playlist data (not saved to DB)."""
    
    youtube_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    image_url = serializers.URLField(allow_blank=True)
    total_tracks = serializers.IntegerField(required=False, default=0)
    owner = serializers.CharField()
    external_url = serializers.URLField()
