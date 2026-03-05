"""Admin configuration for User models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Friendship, Team, TeamJoinRequest, TeamMember, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model without first/last name."""

    list_display = [
        "uuid_short",
        "username",
        "email",
        "is_active",
        "is_staff",
        "coins_display",
        "total_games_played",
        "total_wins",
        "points_display",
        "win_rate_display",
        "created_at",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active", "created_at"]
    search_fields = ["username", "email", "id"]
    ordering = ["-created_at"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Identifiant"),
            {
                "fields": ("id", "username", "email", "email_hash", "password"),
            },
        ),
        (
            _("Profil"),
            {
                "fields": ("avatar", "google_id", "coins_balance"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Statistiques"),
            {
                "fields": (
                    "total_games_played",
                    "total_wins",
                    "total_points",
                ),
                "description": _(
                    "Statistiques calculées automatiquement à chaque fin de partie."
                ),
            },
        ),
        (
            _("RGPD"),
            {
                "fields": ("privacy_policy_accepted_at",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Dates"),
            {"fields": ("last_login", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            _("Créer un compte"),
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    readonly_fields = [
        "id",
        "email_hash",
        "total_games_played",
        "total_wins",
        "total_points",
        "privacy_policy_accepted_at",
        "created_at",
        "updated_at",
        "last_login",
    ]

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Pièces"))
    def coins_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:bold;">🪙 {}</span>',
            obj.coins_balance,
        )

    @admin.display(description=_("Points"))
    def points_display(self, obj):
        return format_html("<strong>{}</strong>", obj.total_points)

    @admin.display(description=_("Win rate"))
    def win_rate_display(self, obj):
        if obj.total_games_played == 0:
            return format_html('<span style="color:#6b7280;">0%</span>')
        rate = (obj.total_wins / obj.total_games_played) * 100
        color = "#10b981" if rate >= 50 else "#f59e0b" if rate >= 25 else "#6b7280"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}%</span>',
            color,
            f"{rate:.0f}",
        )


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = [
        "uuid_short",
        "from_user",
        "to_user",
        "status_badge",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["from_user__username", "to_user__username", "id"]
    list_per_page = 30
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Relation"),
            {"fields": ("from_user", "to_user", "status")},
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Statut"))
    def status_badge(self, obj):
        colors = {
            "pending": "#3b82f6",
            "accepted": "#10b981",
            "rejected": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    readonly_fields = ["id", "user", "role", "joined_at"]
    fields = ["id", "user", "role", "joined_at"]
    can_delete = False
    show_change_link = True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        "uuid_short",
        "name",
        "owner",
        "member_count",
        "total_games",
        "total_wins",
        "total_points",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["name", "owner__username", "id"]
    inlines = [TeamMemberInline]
    list_per_page = 25
    readonly_fields = [
        "id",
        "total_games",
        "total_wins",
        "total_points",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Informations générales"),
            {
                "fields": ("name", "description", "avatar", "owner"),
            },
        ),
        (
            _("Statistiques"),
            {
                "fields": ("total_games", "total_wins", "total_points"),
                "description": _("Statistiques mises à jour automatiquement."),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Membres"))
    def member_count(self, obj):
        return obj.memberships.count()


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = [
        "uuid_short",
        "user",
        "team",
        "status_badge",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["user__username", "team__name", "id"]
    list_per_page = 30
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Demande"),
            {"fields": ("user", "team", "status")},
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @admin.display(description=_("UUID"))
    def uuid_short(self, obj):
        short = str(obj.id)[:8]
        return format_html(
            '<span title="{}" style="font-family:monospace;font-size:11px;'
            'color:#6b7280;">{}</span>',
            obj.id,
            short,
        )

    @admin.display(description=_("Statut"))
    def status_badge(self, obj):
        colors = {
            "pending": "#3b82f6",
            "approved": "#10b981",
            "rejected": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
