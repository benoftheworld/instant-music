"""
Admin configuration for playlists app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
# Playlist/Track models removed; admin entries deleted


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
            """
            Playlists admin helpers removed.

            DB-backed `Playlist` and `Track` admin classes were deleted because the
            underlying models were removed. The app now only exposes external search
            helper endpoints and does not register playlist/track models in admin.
            """
class TrackAdmin(admin.ModelAdmin):
