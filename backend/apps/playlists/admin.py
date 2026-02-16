"""
Admin configuration for playlists app.
"""
from django.contrib import admin
from .models import Playlist, Track


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'youtube_id', 'owner', 'total_tracks', 'created_at']
    search_fields = ['name', 'youtube_id', 'owner']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'youtube_id', 'album', 'duration_ms', 'created_at']
    search_fields = ['name', 'youtube_id']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
