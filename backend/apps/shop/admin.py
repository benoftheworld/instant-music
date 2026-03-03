"""
Configuration de l'admin Django pour la boutique.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import GameBonus, ShopItem, UserInventory


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "item_type",
        "bonus_type",
        "cost",
        "stock",
        "is_event_only",
        "is_available",
        "sort_order",
    ]
    list_filter = ["item_type", "is_event_only", "is_available"]
    list_editable = ["cost", "is_available", "sort_order"]
    search_fields = ["name", "description"]
    ordering = ["sort_order", "name"]
    fieldsets = (
        (
            None,
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
    )


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ["user", "item", "quantity", "purchased_at"]
    list_filter = ["item__item_type"]
    search_fields = ["user__username", "item__name"]
    raw_id_fields = ["user", "item"]
    readonly_fields = ["purchased_at"]


@admin.register(GameBonus)
class GameBonusAdmin(admin.ModelAdmin):
    list_display = [
        "player_username",
        "game_room",
        "bonus_type",
        "round_number",
        "activated_at",
        "is_used",
    ]
    list_filter = ["bonus_type", "is_used"]
    search_fields = ["player__user__username", "game__room_code"]
    readonly_fields = ["activated_at", "used_at"]

    def player_username(self, obj):
        return obj.player.user.username

    player_username.short_description = _("Joueur")

    def game_room(self, obj):
        return obj.game.room_code

    game_room.short_description = _("Salle")
