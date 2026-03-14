"""Configuration de l'admin Django pour la boutique."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import GameBonus, ShopItem, UserInventory


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    """Administration des articles de la boutique."""

    list_display = [
        "uuid_short",
        "name",
        "item_type",
        "bonus_type",
        "cost",
        "stock_display",
        "is_event_only",
        "is_available",
        "sort_order",
        "created_at",
    ]
    list_filter = ["item_type", "is_event_only", "is_available"]
    list_editable = ["cost", "is_available", "sort_order"]
    search_fields = ["name", "description", "id"]
    ordering = ["sort_order", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Article"),
            {
                "fields": (
                    "name",
                    "description",
                    "icon",
                    "item_type",
                    "bonus_type",
                )
            },
        ),
        (
            _("Prix & stock"),
            {
                "fields": (
                    "cost",
                    "stock",
                    "is_event_only",
                    "is_available",
                    "sort_order",
                )
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at")},
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

    @admin.display(description=_("Stock"))
    def stock_display(self, obj):
        """Return a formatted stock count or an infinity symbol for unlimited stock."""
        if obj.stock is None:
            return format_html('<span style="color:#10b981;font-weight:bold;">∞</span>')
        if obj.stock == 0:
            return format_html('<span style="color:#ef4444;font-weight:bold;">0</span>')
        return obj.stock


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    """Administration de l'inventaire des utilisateurs."""

    list_display = [
        "uuid_short",
        "user",
        "item",
        "quantity",
        "purchased_at",
    ]
    list_filter = ["item__item_type", "purchased_at"]
    search_fields = ["user__username", "item__name", "id"]
    raw_id_fields = ["user", "item"]
    readonly_fields = ["id", "user", "item", "purchased_at"]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Inventaire"),
            {"fields": ("user", "item", "quantity")},
        ),
        (
            _("Dates"),
            {"fields": ("purchased_at",)},
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


@admin.register(GameBonus)
class GameBonusAdmin(admin.ModelAdmin):
    """Administration des bonus de partie."""

    list_display = [
        "uuid_short",
        "player_username",
        "game_room_link",
        "bonus_type_badge",
        "round_number",
        "activated_at",
        "is_used",
        "used_at",
    ]
    list_filter = ["bonus_type", "is_used", "activated_at"]
    search_fields = ["player__user__username", "game__room_code", "id"]
    readonly_fields = [
        "id",
        "game",
        "player",
        "bonus_type",
        "round_number",
        "activated_at",
        "is_used",
        "used_at",
    ]

    fieldsets = (
        (
            _("Identifiant"),
            {"fields": ("id",)},
        ),
        (
            _("Contexte"),
            {"fields": ("game", "player", "bonus_type", "round_number")},
        ),
        (
            _("Utilisation"),
            {"fields": ("is_used", "used_at")},
        ),
        (
            _("Dates"),
            {"fields": ("activated_at",)},
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

    @admin.display(description=_("Joueur"))
    def player_username(self, obj):
        """Return the username of the player who used the bonus."""
        return obj.player.user.username

    @admin.display(description=_("Salle"))
    def game_room_link(self, obj):
        """Return an admin link to the related game room."""
        url = reverse("admin:games_game_change", args=[obj.game.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.game.room_code,
        )

    @admin.display(description=_("Bonus"))
    def bonus_type_badge(self, obj):
        """Return a colored badge for the bonus type."""
        colors = {
            "double_points": "#8b5cf6",
            "max_points": "#ec4899",
            "time_bonus": "#3b82f6",
            "fifty_fifty": "#f59e0b",
            "steal": "#ef4444",
            "shield": "#10b981",
        }
        color = colors.get(obj.bonus_type, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            color,
            obj.get_bonus_type_display(),
        )
