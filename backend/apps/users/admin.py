"""
Admin configuration for User models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, Friendship, Team, TeamMember


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model without first/last name."""

    list_display = [
        "username",
        "email",
        "is_staff",
        "total_games_played",
        "total_wins",
        "points_display",
        "win_rate_display",
        "created_at",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active", "created_at"]
    search_fields = ["username", "email"]
    ordering = ["-created_at"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
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
        (_("Profil"), {"fields": ("avatar", "google_id")}),
        (
            _("Statistiques"),
            {"fields": ("total_games_played", "total_wins", "total_points")},
        ),
        (_("Dates"), {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at", "last_login"]

    def points_display(self, obj):
        return format_html("<strong>{}</strong>", obj.total_points)

    points_display.short_description = _("Points")

    def win_rate_display(self, obj):
        rate = obj.win_rate
        color = (
            "#10b981" if rate >= 50 else "#f59e0b" if rate >= 25 else "#6b7280"
        )
        return format_html(
            '<span style="color:{}; font-weight:bold;">{:.0f}%</span>',
            color,
            rate,
        )

    win_rate_display.short_description = _("Win rate")


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user", "status_badge", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["from_user__username", "to_user__username"]
    list_per_page = 30

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

    status_badge.short_description = _("Statut")


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    readonly_fields = ["joined_at"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "owner",
        "member_count",
        "total_games",
        "total_wins",
        "total_points",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["name", "owner__username"]
    inlines = [TeamMemberInline]
    list_per_page = 25

    def member_count(self, obj):
        return obj.memberships.count()

    member_count.short_description = _("Membres")
