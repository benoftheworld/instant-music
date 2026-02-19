"""
Admin configuration for playlists app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Playlist, Track


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "youtube_link",
        "owner",
        "total_tracks",
        "created_at",
    ]
    search_fields = ["name", "youtube_id", "owner"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 25

    def youtube_link(self, obj):
        return format_html(
            '<a href="https://www.youtube.com/playlist?list={}" target="_blank" '
            'style="color:#dc2626;">\u25b6 {}</a>',
            obj.youtube_id,
            obj.youtube_id[:20],
        )

    youtube_link.short_description = _("YouTube")


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "artists_display",
        "album",
        "duration_display",
        "created_at",
    ]
    search_fields = ["name", "youtube_id"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 30

    def artists_display(self, obj):
        return ", ".join(obj.artists) if obj.artists else "\u2014"

    artists_display.short_description = _("Artistes")

    def duration_display(self, obj):
        secs = obj.duration_ms // 1000
        m, s = divmod(secs, 60)
        return f"{m}:{s:02d}"

    duration_display.short_description = _("Dur\u00e9e")
