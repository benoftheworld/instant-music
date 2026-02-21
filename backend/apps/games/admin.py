"""
Admin configuration for games.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Game, GamePlayer, GameRound, GameAnswer, KaraokeSong


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 0
    readonly_fields = ["user", "score", "rank", "is_connected", "joined_at"]
    fields = ["user", "score", "rank", "is_connected", "joined_at"]
    can_delete = False
    show_change_link = True


class GameRoundInline(admin.TabularInline):
    model = GameRound
    extra = 0
    readonly_fields = [
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "started_at",
        "ended_at",
    ]
    fields = [
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "started_at",
        "ended_at",
    ]
    can_delete = False
    show_change_link = True


# TrackCache admin removed — model no longer present.
                    "score_display_duration",
                ),
            },
        ),
        (
            _("Playlist"),
            {
                "fields": ("playlist_id",),
            },
        ),
        (
            _("Karaoké"),
            {
                "fields": ("karaoke_song", "karaoke_track"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("created_at", "started_at", "finished_at"),
            },
        ),
    )

    def player_count(self, obj):
        count = obj.players.count()
        return format_html(
            '<span style="font-weight:bold;">{}/{}</span>',
            count,
            obj.max_players,
        )

    player_count.short_description = _("Joueurs")

    def name_display(self, obj):
        return obj.name or "—"

    name_display.short_description = _("Nom")

    def mode_badge(self, obj):
        colors = {
            "classique": "#6366f1",
            "rapide": "#f59e0b",
            "generation": "#10b981",
            "paroles": "#8b5cf6",
            "karaoke": "#ec4899",
        }
        color = colors.get(obj.mode, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_mode_display(),
        )

    mode_badge.short_description = _("Mode")

    def status_badge(self, obj):
        colors = {
            "waiting": "#3b82f6",
            "in_progress": "#f59e0b",
            "finished": "#10b981",
            "cancelled": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Statut")


class GameAnswerInline(admin.TabularInline):
    model = GameAnswer
    extra = 0
    readonly_fields = [
        "player",
        "answer",
        "is_correct",
        "points_earned",
        "response_time",
        "answered_at",
    ]
    fields = [
        "player",
        "answer",
        "is_correct",
        "points_earned",
        "response_time",
        "answered_at",
    ]
    can_delete = False


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    """Admin for GamePlayer model."""

    list_display = [
        "user",
        "game_link",
        "score",
        "rank",
        "is_connected",
        "joined_at",
    ]
    list_filter = ["is_connected", "joined_at"]
    search_fields = ["user__username", "game__room_code"]
    list_per_page = 30
    raw_id_fields = ["user", "game"]

    def game_link(self, obj):
        return format_html(
            '<a href="/admin/games/game/{}/change/">{}</a>',
            obj.game.pk,
            obj.game.room_code,
        )

    game_link.short_description = _("Partie")


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    """Admin for GameRound model."""

    list_display = [
        "game",
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "answer_count",
        "started_at",
    ]
    list_filter = ["question_type", "started_at"]
    search_fields = ["game__room_code", "track_name", "artist_name"]
    list_per_page = 30
    raw_id_fields = ["game"]
    readonly_fields = ["started_at", "ended_at"]
    inlines = [GameAnswerInline]

    fieldsets = (
        (
            _("Informations générales"),
            {
                "fields": (
                    "game",
                    "round_number",
                    "question_type",
                    "question_text",
                ),
            },
        ),
        (
            _("Morceau"),
            {
                "fields": (
                    "track_id",
                    "track_name",
                    "artist_name",
                    "correct_answer",
                    "options",
                    "preview_url",
                ),
            },
        ),
        (
            _("Paramètres"),
            {
                "fields": ("duration", "extra_data"),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("started_at", "ended_at"),
            },
        ),
    )

    def answer_count(self, obj):
        return obj.answers.count()

    answer_count.short_description = _("Réponses")


@admin.register(GameAnswer)
class GameAnswerAdmin(admin.ModelAdmin):
    """Admin for GameAnswer model."""

    list_display = [
        "player",
        "round",
        "answer",
        "correct_badge",
        "points_earned",
        "response_time_display",
        "answered_at",
    ]
    list_filter = ["is_correct", "answered_at"]
    search_fields = ["player__user__username", "round__game__room_code"]
    list_per_page = 50
    raw_id_fields = ["player", "round"]

    def correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color:#10b981; font-weight:bold;">✓ Correct</span>'
            )
        return format_html('<span style="color:#ef4444;">✗ Faux</span>')

    correct_badge.short_description = _("Résultat")

    def response_time_display(self, obj):
        return f"{obj.response_time:.1f}s"

    response_time_display.short_description = _("Temps")


try:
    from .models import TrackCache  # may be removed in future migration
except Exception:
    TrackCache = None

if TrackCache:
    @admin.register(TrackCache)
    class TrackCacheAdmin(admin.ModelAdmin):
        """Admin for TrackCache — browse and manage the local track/lyrics cache."""

        list_display = [
            "artist_name",
            "track_name",
            "has_youtube",
            "has_synced",
            "has_plain",
            "updated_at",
        ]
        search_fields = ["artist_name", "track_name", "youtube_video_id"]
        list_filter = ["updated_at"]
        readonly_fields = ["artist_key", "track_key", "created_at", "updated_at"]
        list_per_page = 50
        ordering = ["-updated_at"]

        fieldsets = (
            (
                _("Identité"),
                {
                    "fields": (
                        "artist_name",
                        "artist_key",
                        "track_name",
                        "track_key",
                    )
                },
            ),
            (
                _("YouTube"),
                {
                    "fields": (
                        "youtube_video_id",
                        "video_duration_ms",
                        "album_image",
                    )
                },
            ),
            (
                _("Paroles synchros"),
                {"fields": ("synced_lyrics",)},
            ),
            (
                _("Paroles brutes"),
                {"fields": ("plain_lyrics",)},
            ),
            (
                _("Dates"),
                {"fields": ("created_at", "updated_at")},
            ),
        )

        def has_youtube(self, obj):
            if obj.youtube_video_id:
                return format_html(
                    '<a href="https://youtu.be/{0}" target="_blank" '
                    'style="color:#ef4444; font-weight:600">▶ {0}</a>',
                    obj.youtube_video_id,
                )
            return format_html('<span style="color:#9ca3af">—</span>')

        has_youtube.short_description = _("YouTube")

    def has_synced(self, obj):
        n = len(obj.synced_lyrics) if obj.synced_lyrics else 0
        if n:
            return format_html(
                '<span style="color:#10b981; font-weight:600">✓ {} lignes</span>',
                n,
            )
        return format_html('<span style="color:#9ca3af">—</span>')

    has_synced.short_description = _("Synchro")

    def has_plain(self, obj):
        if obj.plain_lyrics:
            words = len(obj.plain_lyrics.split())
            return format_html(
                '<span style="color:#6366f1">✓ ~{} mots</span>', words
            )
        return format_html('<span style="color:#9ca3af">—</span>')

    has_plain.short_description = _("Paroles brutes")


@admin.register(KaraokeSong)
class KaraokeSongAdmin(admin.ModelAdmin):
    """Admin pour le catalogue de morceaux karaoké."""

    list_display = [
        "artist",
        "title",
        "youtube_link",
        "lrclib_id",
        "duration_display",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "artist", "youtube_video_id"]
    list_editable = ["is_active"]
    list_per_page = 50
    ordering = ["artist", "title"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Morceau"),
            {
                "fields": ("title", "artist", "album_image_url", "duration_ms", "is_active"),
            },
        ),
        (
            _("Sources"),
            {
                "fields": ("youtube_video_id", "lrclib_id"),
                "description": _(
                    "youtube_video_id : copier l'ID depuis l'URL YouTube (ex: dQw4w9WgXcQ). "
                    "lrclib_id : ID numérique sur lrclib.net — laisser vide pour une recherche "
                    "automatique par titre/artiste."
                ),
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def youtube_link(self, obj):
        if obj.youtube_video_id:
            return format_html(
                '<a href="https://youtu.be/{0}" target="_blank" '
                'style="color:#ef4444; font-weight:600">▶ {0}</a>',
                obj.youtube_video_id,
            )
        return "—"

    youtube_link.short_description = _("YouTube")

    def duration_display(self, obj):
        if not obj.duration_ms:
            return "—"
        total_seconds = obj.duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    duration_display.short_description = _("Durée")
