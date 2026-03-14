"""Admin configuration for games."""

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Game,
    GameAnswer,
    GameInvitation,
    GamePlayer,
    GameRound,
    KaraokeSong,
)


class GamePlayerInline(admin.TabularInline):
    """Inline d'administration des joueurs d'une partie."""

    model = GamePlayer
    extra = 0
    readonly_fields = [
        "user",
        "score",
        "rank",
        "consecutive_correct",
        "is_connected",
        "joined_at",
    ]
    fields = [
        "user",
        "score",
        "rank",
        "consecutive_correct",
        "is_connected",
        "joined_at",
    ]
    can_delete = False
    show_change_link = True


class GameRoundInline(admin.TabularInline):
    """Inline d'administration des rounds d'une partie."""

    model = GameRound
    extra = 0
    readonly_fields = [
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "correct_answer",
        "started_at",
        "ended_at",
    ]
    fields = [
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "correct_answer",
        "started_at",
        "ended_at",
    ]
    can_delete = False
    show_change_link = True


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin for Game model."""

    list_display = [
        "uuid_short",
        "room_code",
        "name_display",
        "host",
        "mode_badge",
        "status_badge",
        "player_count",
        "is_public",
        "created_at",
    ]
    list_filter = ["status", "mode", "is_online", "is_public", "created_at"]
    search_fields = ["room_code", "name", "host__username", "id"]
    list_per_page = 30
    raw_id_fields = ["host", "karaoke_song"]
    readonly_fields = [
        "id",
        "room_code",
        "created_at",
        "started_at",
        "finished_at",
    ]
    inlines = [GamePlayerInline, GameRoundInline]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id", "room_code")},
        ),
        (
            _("Informations générales"),
            {"fields": ("name", "host", "status")},
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
                    "is_public",
                ),
            },
        ),
        (
            _("Playlist & Karaoké"),
            {
                "fields": (
                    "playlist_id",
                    "playlist_name",
                    "playlist_image_url",
                    "karaoke_song",
                    "karaoke_track",
                ),
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

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Joueurs"))
    def player_count(self, obj):
        """Return the current player count relative to max players."""
        count = obj.players.count()
        return format_html(
            '<span style="font-weight:bold;">{}/{}</span>',
            count,
            obj.max_players,
        )

    @admin.display(description=_("Nom"))
    def name_display(self, obj):
        """Return the game name or an em dash if unset."""
        return obj.name or "—"

    @admin.display(description=_("Mode"))
    def mode_badge(self, obj):
        """Return a colored badge for the game mode."""
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

    @admin.display(description=_("Statut"))
    def status_badge(self, obj):
        """Return a colored badge for the game status."""
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


class GameAnswerInline(admin.TabularInline):
    """Inline d'administration des réponses d'une partie."""

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
        "uuid_short",
        "user",
        "game_link",
        "score",
        "rank",
        "consecutive_correct",
        "is_connected",
        "joined_at",
    ]
    list_filter = ["is_connected", "joined_at"]
    search_fields = ["user__username", "game__room_code", "id"]
    list_per_page = 30
    raw_id_fields = ["user", "game"]
    readonly_fields = [
        "id",
        "score",
        "rank",
        "consecutive_correct",
        "joined_at",
    ]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Joueur & Partie"),
            {"fields": ("user", "game")},
        ),
        (
            _("Résultats"),
            {
                "fields": (
                    "score",
                    "rank",
                    "consecutive_correct",
                    "is_connected",
                ),
            },
        ),
        (
            _("Dates"),
            {"fields": ("joined_at",)},
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Partie"))
    def game_link(self, obj):
        """Return an admin link to the related game."""
        url = reverse("admin:games_game_change", args=[obj.game.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.game.room_code,
        )


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    """Admin for GameRound model."""

    list_display = [
        "uuid_short",
        "game",
        "round_number",
        "track_name",
        "artist_name",
        "question_type",
        "answer_count",
        "started_at",
    ]
    list_filter = ["question_type", "started_at"]
    search_fields = ["game__room_code", "track_name", "artist_name", "id"]
    list_per_page = 30
    raw_id_fields = ["game"]
    readonly_fields = [
        "id",
        "round_number",
        "track_id",
        "track_name",
        "artist_name",
        "correct_answer",
        "options",
        "preview_url",
        "question_type",
        "question_text",
        "extra_data",
        "duration",
        "started_at",
        "ended_at",
    ]
    inlines = [GameAnswerInline]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
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
                "classes": ("collapse",),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("started_at", "ended_at"),
            },
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Réponses"))
    def answer_count(self, obj):
        """Return the number of answers submitted for this round."""
        return obj.answers.count()


@admin.register(GameAnswer)
class GameAnswerAdmin(admin.ModelAdmin):
    """Admin for GameAnswer model."""

    list_display = [
        "uuid_short",
        "player",
        "round",
        "answer",
        "correct_badge",
        "points_earned",
        "streak_bonus",
        "response_time_display",
        "answered_at",
    ]
    list_filter = ["is_correct", "answered_at"]
    search_fields = ["player__user__username", "round__game__room_code", "id"]
    list_per_page = 50
    raw_id_fields = ["player", "round"]
    readonly_fields = [
        "id",
        "player",
        "round",
        "answer",
        "is_correct",
        "points_earned",
        "streak_bonus",
        "response_time",
        "answered_at",
    ]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Contexte"),
            {"fields": ("player", "round")},
        ),
        (
            _("Réponse"),
            {
                "fields": (
                    "answer",
                    "is_correct",
                    "points_earned",
                    "streak_bonus",
                    "response_time",
                ),
            },
        ),
        (
            _("Dates"),
            {"fields": ("answered_at",)},
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Résultat"))
    def correct_badge(self, obj):
        """Return a styled badge indicating whether the answer was correct."""
        if obj.is_correct:
            return format_html(
                '<span style="color:#10b981; font-weight:bold;">✓ Correct</span>'
            )
        return format_html('<span style="color:#ef4444;">✗ Faux</span>')

    @admin.display(description=_("Temps"))
    def response_time_display(self, obj):
        """Return the response time formatted as a string with one decimal."""
        return f"{obj.response_time:.1f}s"


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
                    "youtube_video_id : copier l'ID depuis l'URL YouTube"
                    " (ex: dQw4w9WgXcQ). "
                    "lrclib_id : ID numérique sur lrclib.net — laisser vide"
                    " pour une recherche automatique par titre/artiste."
                    " Utilisez le bouton ci-dessous pour rechercher."
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
        """Return admin URLs, including the custom LRCLib search view."""
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

    _ADMIN_LRCLIB_TIMEOUT: int = 8  # seconds — shorter than game path (12s)

    def _lrclib_admin_search(self, q: str):
        """Perform a direct /api/search call to lrclib.net for admin use.

        Bypasses the circuit breaker (admin explicitly wants to probe) and
        uses the same SSL workaround as lyrics_service._lrclib_fetch but
        with a shorter timeout suited for a synchronous admin HTTP request.

        Returns:
            list of result dicts, or None on error.
            A string error message if a known failure occurs.

        """
        import json
        import ssl
        import urllib.error
        import urllib.request
        from urllib.parse import urlencode

        from apps.games.lyrics_service import _lrclib_ssl_context

        url = f"https://lrclib.net/api/search?{urlencode({'q': q})}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "InstantMusic/1.0 (admin lyrics search)"},
        )
        try:
            with urllib.request.urlopen(  # nosec B310
                req,
                context=_lrclib_ssl_context(),
                timeout=self._ADMIN_LRCLIB_TIMEOUT,
            ) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
                return f"HTTP {resp.status} reçu de lrclib.net."
        except ssl.SSLError as exc:
            return f"Erreur SSL avec lrclib.net : {exc}"
        except TimeoutError:
            return (
                f"Délai dépassé ({self._ADMIN_LRCLIB_TIMEOUT}s) — "
                "lrclib.net ne répond pas."
            )
        except urllib.error.HTTPError as exc:
            return f"lrclib.net a retourné HTTP {exc.code} : {exc.reason}"
        except urllib.error.URLError as exc:
            return f"Impossible de joindre lrclib.net : {exc.reason}"
        except Exception as exc:  # noqa: BLE001
            return f"Erreur inattendue : {exc}"

    def lrclib_search_view(self, request, object_id):
        """Handle the lrclib.net candidate search for a KaraokeSong.

        GET  — display search form pre-filled with artist+title; show results
               when query params are present.
        POST — save the selected lrclib_id and redirect back to the change page.
        """
        from django.core.cache import cache

        from apps.games.lyrics_service import _LRCLIB_DOWN_KEY

        song = self.get_object(request, object_id)
        if song is None:
            self.message_user(request, "Morceau introuvable.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:games_karaokesong_changelist"))

        # POST — assign chosen ID or reset circuit breaker
        if request.method == "POST":
            if "reset_circuit_breaker" in request.POST:
                cache.delete(_LRCLIB_DOWN_KEY)
                self.message_user(
                    request,
                    "🔄 Circuit breaker LRCLib réinitialisé.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())

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
                self.message_user(request, "ID invalide.", level=messages.ERROR)
            return HttpResponseRedirect(
                reverse("admin:games_karaokesong_change", args=[object_id])
            )

        # GET — run search and render results
        query_artist = request.GET.get("artist", song.artist)
        query_title = request.GET.get("title", song.title)
        query_free = request.GET.get("q", "").strip()

        results = None
        error = None
        circuit_open = bool(cache.get(_LRCLIB_DOWN_KEY))

        # Only search when at least one search param was explicitly submitted
        search_submitted = any(k in request.GET for k in ("artist", "title", "q"))
        if search_submitted:
            q_string = query_free or f"{query_artist} {query_title}".strip()
            if not q_string:
                error = "Veuillez saisir au moins un terme de recherche."
                results: list[str] = []  # type: ignore[no-redef]
            else:
                raw = self._lrclib_admin_search(q_string)
                if isinstance(raw, str):
                    # _lrclib_admin_search returned an error message
                    error = raw
                    results = []  # type: ignore[var-annotated]
                elif isinstance(raw, list):
                    results = []
                    for item in raw:
                        dur_s = item.get("duration", 0) or 0
                        total_s = int(dur_s)
                        mins = total_s // 60
                        secs = total_s % 60
                        results.append(
                            {
                                "id": item.get("id"),
                                "name": item.get("trackName", "—"),
                                "artist_name": item.get("artistName", "—"),
                                "album_name": item.get("albumName", ""),
                                "duration_display": (
                                    f"{mins}:{secs:02d}" if dur_s else "—"
                                ),
                                "has_synced": bool(item.get("syncedLyrics")),
                            }
                        )
                else:
                    error = "Réponse inattendue de lrclib.net."
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
            "circuit_open": circuit_open,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/games/karaokesong/lrclib_search.html",
            context,
        )

    # ── Display helpers ──────────────────────────────────────────────────────

    def lrclib_search_button(self, obj):
        """Render a button linking to the LRCLib search view."""
        if obj and obj.pk:
            url = reverse("admin:games_karaokesong_lrclib_search", args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" style="'
                "background:#417690;color:#fff;padding:6px 16px;"
                "border-radius:6px;text-decoration:none;font-size:13px;"
                'font-weight:600;display:inline-block;">'
                "🔍 Rechercher sur LRCLib.net</a>",
                url,
            )
        return format_html(
            '<em style="color:#999;">Sauvegardez d\'abord le morceau'
            " pour activer la recherche.</em>"
        )

    lrclib_search_button.short_description = _("Outil LRCLib")  # type: ignore[attr-defined]

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("YouTube"))
    def youtube_link(self, obj):
        """Return a link to the YouTube video, or a dash if unset."""
        if obj.youtube_video_id:
            return format_html(
                '<a href="https://youtu.be/{0}" target="_blank" '
                'style="color:#ef4444; font-weight:600">▶ {0}</a>',
                obj.youtube_video_id,
            )
        return "—"

    @admin.display(description=_("Durée"))
    def duration_display(self, obj):
        """Return the formatted duration as mm:ss."""
        if not obj.duration_ms:
            return "—"
        total_seconds = obj.duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"


@admin.register(GameInvitation)
class GameInvitationAdmin(admin.ModelAdmin):
    """Admin for GameInvitation model."""

    list_display = [
        "uuid_short",
        "sender",
        "recipient",
        "game_link",
        "status_badge",
        "created_at",
        "expires_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "sender__username",
        "recipient__username",
        "game__room_code",
        "id",
    ]
    readonly_fields = [
        "id",
        "sender",
        "recipient",
        "game",
        "created_at",
        "expires_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 30

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Invitation"),
            {"fields": ("sender", "recipient", "game", "status")},
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "expires_at")},
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        """Return a shortened UUID for display."""
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Partie"))
    def game_link(self, obj):
        """Return an admin link to the related game."""
        url = reverse("admin:games_game_change", args=[obj.game.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.game.room_code,
        )

    @admin.display(description=_("Statut"))
    def status_badge(self, obj):
        """Return a colored badge for the invitation status."""
        colors = {
            "pending": "#3b82f6",
            "accepted": "#10b981",
            "declined": "#f59e0b",
            "expired": "#6b7280",
            "cancelled": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
