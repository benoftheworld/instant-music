"""
Admin for playlists.
"""
from django.contrib import admin
from .models import Playlist


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'spotify_id', 'total_tracks', 'updated_at']
    search_fields = ['name', 'spotify_id']
