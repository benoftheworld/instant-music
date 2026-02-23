"""
Django admin configuration for apps/administration.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Admin pour la configuration globale du site.
    Singleton — une seule ligne possible.
    """

    fieldsets = (
        (
            _("🔴 Mode Maintenance"),
            {
                "fields": (
                    "maintenance_mode",
                    "maintenance_title",
                    "maintenance_message",
                ),
                "description": _(
                    "Quand le mode maintenance est activé, toutes les requêtes "
                    "vers le site (sauf l'admin) reçoivent une erreur 503. "
                    "Le frontend affiche le titre et le message configurés ici."
                ),
            },
        ),
        (
            _("📢 Bandeau d'information"),
            {
                "fields": (
                    "banner_enabled",
                    "banner_message",
                    "banner_color",
                    "banner_dismissible",
                ),
                "description": _(
                    "Un bandeau visible en haut du site pour communiquer avec les joueurs "
                    "(annonce de maintenance prévue, nouvelle fonctionnalité, etc.)."
                ),
            },
        ),
        (
            _("Métadonnées"),
            {
                "fields": ("updated_at",),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["updated_at", "status_overview"]

    def get_fieldsets(self, request, obj=None):
        """Add the status overview as the first section."""
        base = list(super().get_fieldsets(request, obj))
        base.insert(
            0,
            (
                _("État actuel"),
                {"fields": ("status_overview",)},
            ),
        )
        return base

    def status_overview(self, obj):
        if obj is None:
            return "—"
        parts = []
        if obj.maintenance_mode:
            parts.append(
                '<span style="background:#ef4444;color:#fff;padding:4px 12px;'
                'border-radius:6px;font-weight:bold;">🔴 MAINTENANCE ACTIVE</span>'
            )
        else:
            parts.append(
                '<span style="background:#10b981;color:#fff;padding:4px 12px;'
                'border-radius:6px;font-weight:bold;">🟢 Site en ligne</span>'
            )
        if obj.banner_enabled:
            color_map = {
                "info": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
            }
            bg = color_map.get(obj.banner_color, "#6b7280")
            parts.append(
                f'&nbsp;&nbsp;<span style="background:{bg};color:#fff;padding:4px 12px;'
                f'border-radius:6px;font-weight:bold;">📢 Bandeau actif</span>'
            )
        return format_html("&nbsp;".join(parts))

    status_overview.short_description = _("État")

    def has_add_permission(self, request) -> bool:
        """Only allow creation if the singleton doesn't exist yet."""
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prevent deletion of the singleton."""
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.maintenance_mode:
            self.message_user(
                request,
                "⚠️ Mode maintenance ACTIVÉ — le site est inaccessible aux joueurs.",
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                "✅ Configuration sauvegardée. Le site est en ligne.",
                level=messages.SUCCESS,
            )
