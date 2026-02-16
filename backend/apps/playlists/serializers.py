"""
Serializers for playlists app.
"""
from rest_framework import serializers
from .models import Playlist, Track, SpotifyToken


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for Playlist model."""
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'spotify_id', 'name', 'description', 
            'image_url', 'total_tracks', 'owner', 'external_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrackSerializer(serializers.ModelSerializer):
    """Serializer for Track model."""
    
    artists_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Track
        fields = [
            'id', 'spotify_id', 'name', 'artists', 'artists_display',
            'album', 'album_image', 'duration_ms', 'preview_url',
            'external_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_artists_display(self, obj) -> str:
        """Get comma-separated artist names."""
        return ', '.join(obj.artists) if obj.artists else 'Unknown'


class SpotifyPlaylistSerializer(serializers.Serializer):
    """Serializer for Spotify API playlist data (not saved to DB)."""
    
    spotify_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    image_url = serializers.URLField(allow_blank=True)
    total_tracks = serializers.IntegerField()
    owner = serializers.CharField()
    external_url = serializers.URLField()


class SpotifyTrackSerializer(serializers.Serializer):
    """Serializer for Spotify API track data (not saved to DB)."""
    
    spotify_id = serializers.CharField()
    name = serializers.CharField()
    artists = serializers.ListField(child=serializers.CharField())
    album = serializers.CharField()
    album_image = serializers.URLField(allow_blank=True)
    duration_ms = serializers.IntegerField()
    preview_url = serializers.URLField(allow_blank=True, allow_null=True)
    external_url = serializers.URLField()


class SpotifyTokenSerializer(serializers.ModelSerializer):
    """Serializer for SpotifyToken model."""
    
    is_expired = serializers.BooleanField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SpotifyToken
        fields = [
            'id', 'username', 'token_type', 'expires_at', 
            'scope', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        # Don't expose actual tokens in API responses
