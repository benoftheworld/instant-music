"""
Admin for achievements.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Achievement, UserAchievement


class UserAchievementInline(admin.TabularInline):
    """Inline for displaying which users have unlocked an achievement."""

    model = UserAchievement
    extra = 0
    readonly_fields = ["id", "user", "unlocked_at"]
    fields = ["id", "user", "unlocked_at"]
    can_delete = False


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Admin for managing achievements."""

    list_display = [
        "uuid_short",
        "name",
        "points_badge",
        "condition_type",
        "condition_value",
        "unlock_count",
    ]
    search_fields = ["name", "description", "id"]
    list_per_page = 25
    readonly_fields = ["id"]
    inlines = [UserAchievementInline]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Succès"),
            {
                "fields": ("name", "description", "icon", "points"),
            },
        ),
        (
            _("Condition"),
            {
                "fields": ("condition_type", "condition_value"),
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

    @admin.display(description=_("Points"))
    def points_badge(self, obj):
        return format_html(
            '<span style="background:#8b5cf6; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px; font-weight:bold;">{} pts</span>',
            obj.points,
        )

    @admin.display(description=_("Débloqué par"))
    def unlock_count(self, obj):
        return obj.userachievement_set.count()


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Admin for managing user achievements."""

    list_display = ["uuid_short", "user", "achievement", "unlocked_at"]
    list_filter = ["unlocked_at", "achievement"]
    search_fields = ["user__username", "achievement__name", "id"]
    list_per_page = 30
    raw_id_fields = ["user"]
    readonly_fields = ["id", "user", "achievement", "unlocked_at"]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Succès débloqué"),
            {"fields": ("user", "achievement")},
        ),
        (
            _("Dates"),
            {"fields": ("unlocked_at",)},
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
