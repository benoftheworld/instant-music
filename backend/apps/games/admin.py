"""
Admin configuration for games.
"""

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
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


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin for Game model."""

    list_display = [
        "room_code",
        "name_display",
        "host",
        "mode_badge",
        "status_badge",
        "player_count",
        "created_at",
    ]
    list_filter = ["status", "mode", "is_online", "created_at"]
    search_fields = ["room_code", "name", "host__username"]
    list_per_page = 30
    raw_id_fields = ["host", "karaoke_song"]
    readonly_fields = ["room_code", "created_at", "started_at", "finished_at"]
    inlines = [GamePlayerInline, GameRoundInline]

    fieldsets = (
        (
            _("Informations générales"),
            {"fields": ("room_code", "name", "host", "status")},
        ),
        (
            _("Configuration du jeu"),
            {
                "fields": (
                    "mode",
                    "answer_mode",
                    "guess_target",
                    "max_players",
                    "num_rounds",
                    "is_online",
                ),
            },
        ),
        (
            _("Playlist & Karaoké"),
            {
                "fields": ("playlist_id", "karaoke_song", "karaoke_track"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timers"),
            {
                "fields": (
                    "round_duration",
                    "timer_start_round",
                    "score_display_duration",
                    "lyrics_words_count",
                ),
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
    readonly_fields = ["created_at", "updated_at", "lrclib_search_button"]

    fieldsets = (
        (
            _("Morceau"),
            {
                "fields": (
                    "title",
                    "artist",
                    "album_image_url",
                    "duration_ms",
                    "is_active",
                ),
            },
        ),
        (
            _("Sources"),
            {
                "fields": (
                    "youtube_video_id",
                    "lrclib_id",
                    "lrclib_search_button",
                ),
                "description": _(
                    "youtube_video_id : copier l'ID depuis l'URL YouTube (ex: dQw4w9WgXcQ). "
                    "lrclib_id : ID numérique sur lrclib.net — laisser vide pour une recherche "
                    "automatique par titre/artiste. Utilisez le bouton ci-dessous pour rechercher."
                ),
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # ── Custom URLs ──────────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/lrclib-search/",
                self.admin_site.admin_view(self.lrclib_search_view),
                name="games_karaokesong_lrclib_search",
            ),
        ]
        return custom + urls

    # ── LRCLib search view ───────────────────────────────────────────────────

    def lrclib_search_view(self, request, object_id):
        """
        Custom admin view to search lrclib.net candidates for a KaraokeSong.

        GET  — display search form pre-filled with artist+title; show results
               when query params are present.
        POST — save the selected lrclib_id and redirect back to the change page.
        """
        from apps.games.lyrics_service import _lrclib_fetch

        song = self.get_object(request, object_id)
        if song is None:
            self.message_user(
                request, "Morceau introuvable.", level=messages.ERROR
            )
            return HttpResponseRedirect(
                reverse("admin:games_karaokesong_changelist")
            )

        # POST — assign chosen ID
        if request.method == "POST":
            raw_id = request.POST.get("lrclib_id", "").strip()
            if raw_id.isdigit():
                song.lrclib_id = int(raw_id)
                song.save(update_fields=["lrclib_id", "updated_at"])
                self.message_user(
                    request,
                    f"✅ lrclib_id mis à jour : {song.lrclib_id} pour « {song} ».",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request, "ID invalide.", level=messages.ERROR
                )
            return HttpResponseRedirect(
                reverse("admin:games_karaokesong_change", args=[object_id])
            )

        # GET — run search and render results
        query_artist = request.GET.get("artist", song.artist)
        query_title = request.GET.get("title", song.title)
        query_free = request.GET.get("q", "").strip()

        results = None
        error = None

        if request.GET:  # Only search when the form was submitted
            try:
                if query_free:
                    raw = _lrclib_fetch(
                        "https://lrclib.net/api/search",
                        params={"q": query_free},
                    )
                else:
                    q = f"{query_artist} {query_title}".strip()
                    raw = _lrclib_fetch(
                        "https://lrclib.net/api/search",
                        params={"q": q},
                    )

                if raw is None:
                    error = (
                        "LRCLib est inaccessible ou la recherche a échoué. "
                        "Vérifiez la connectivité réseau du serveur."
                    )
                    results = []
                elif isinstance(raw, list):
                    results = []
                    for item in raw:
                        dur_ms = item.get("duration", 0) or 0
                        total_s = dur_ms // 1000
                        mins = total_s // 60
                        secs = total_s % 60
                        results.append(
                            {
                                "id": item.get("id"),
                                "name": item.get("trackName", "—"),
                                "artist_name": item.get("artistName", "—"),
                                "album_name": item.get("albumName", ""),
                                "duration_display": (
                                    f"{mins}:{secs:02d}" if dur_ms else "—"
                                ),
                                "has_synced": bool(item.get("syncedLyrics")),
                            }
                        )
                else:
                    error = "Réponse inattendue de lrclib.net."
                    results = []
            except Exception as exc:  # noqa: BLE001
                error = f"Erreur lors de la recherche : {exc}"
                results = []

        context = {
            **self.admin_site.each_context(request),
            "title": f"Recherche LRCLib — {song}",
            "song": song,
            "query_artist": query_artist,
            "query_title": query_title,
            "query_free": query_free,
            "results": results,
            "error": error,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/games/karaokesong/lrclib_search.html",
            context,
        )

    # ── Display helpers ──────────────────────────────────────────────────────

    def lrclib_search_button(self, obj):
        """Renders a button linking to the LRCLib search view."""
        if obj and obj.pk:
            url = reverse(
                "admin:games_karaokesong_lrclib_search", args=[obj.pk]
            )
            return format_html(
                '<a href="{}" class="button" style="'
                "background:#417690;color:#fff;padding:6px 16px;"
                "border-radius:6px;text-decoration:none;font-size:13px;"
                'font-weight:600;display:inline-block;">'
                "🔍 Rechercher sur LRCLib.net</a>",
                url,
            )
        return format_html(
            '<em style="color:#999;">Sauvegardez d\'abord le morceau pour activer la recherche.</em>'
        )

    lrclib_search_button.short_description = _("Outil LRCLib")

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
