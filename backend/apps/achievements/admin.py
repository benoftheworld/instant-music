"""
Admin for achievements.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Achievement, UserAchievement


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    readonly_fields = ["user", "unlocked_at"]
    can_delete = False


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "points_badge",
        "condition_type",
        "condition_value",
        "unlock_count",
    ]
    search_fields = ["name", "description"]
    list_per_page = 25
    inlines = [UserAchievementInline]

    def points_badge(self, obj):
        return format_html(
            '<span style="background:#8b5cf6; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px; font-weight:bold;">{} pts</span>',
            obj.points,
        )

    points_badge.short_description = _("Points")

    def unlock_count(self, obj):
        return obj.userachievement_set.count()

    unlock_count.short_description = _("D\u00e9bloqu\u00e9 par")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ["user", "achievement", "unlocked_at"]
    list_filter = ["unlocked_at", "achievement"]
    search_fields = ["user__username", "achievement__name"]
    list_per_page = 30
    raw_id_fields = ["user"]
