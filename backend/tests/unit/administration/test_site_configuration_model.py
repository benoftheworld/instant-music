"""Tests unitaires du modèle SiteConfiguration (singleton)."""

from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError

from apps.administration.models import SiteConfiguration
from tests.base import BaseModelUnitTest


class TestSiteConfigurationModel(BaseModelUnitTest):
    """Vérifie les champs, les contraintes singleton et le cache."""

    def get_model_class(self):
        return SiteConfiguration

    # ── maintenance_mode ────────────────────────────────────────────

    def test_maintenance_mode_default(self):
        self.assert_field_default(SiteConfiguration, "maintenance_mode", False)

    def test_maintenance_title_max_length(self):
        self.assert_field_max_length(SiteConfiguration, "maintenance_title", 200)

    def test_maintenance_title_default(self):
        self.assert_field_default(
            SiteConfiguration, "maintenance_title", "Maintenance en cours"
        )

    def test_maintenance_title_blank(self):
        self.assert_field_blank(SiteConfiguration, "maintenance_title", True)

    def test_maintenance_message_blank(self):
        self.assert_field_blank(SiteConfiguration, "maintenance_message", True)

    # ── banner ──────────────────────────────────────────────────────

    def test_banner_color_choices(self):
        self.assert_field_choices(
            SiteConfiguration,
            "banner_color",
            SiteConfiguration.BannerColor.choices,
        )

    def test_banner_color_values(self):
        bc = SiteConfiguration.BannerColor
        assert bc.INFO == "info"
        assert bc.SUCCESS == "success"
        assert bc.WARNING == "warning"
        assert bc.DANGER == "danger"

    def test_banner_color_default(self):
        self.assert_field_default(
            SiteConfiguration,
            "banner_color",
            SiteConfiguration.BannerColor.INFO,
        )

    def test_banner_color_max_length(self):
        self.assert_field_max_length(SiteConfiguration, "banner_color", 10)

    def test_banner_enabled_default(self):
        self.assert_field_default(SiteConfiguration, "banner_enabled", False)

    def test_banner_message_max_length(self):
        self.assert_field_max_length(SiteConfiguration, "banner_message", 500)

    def test_banner_message_blank(self):
        self.assert_field_blank(SiteConfiguration, "banner_message", True)

    def test_banner_dismissible_default(self):
        self.assert_field_default(SiteConfiguration, "banner_dismissible", True)

    # ── updated_at ──────────────────────────────────────────────────

    def test_updated_at_auto_now(self):
        field = SiteConfiguration._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("Configuration du site", "Configuration du site")

    # ── clean: singleton constraint ─────────────────────────────────

    def test_clean_pk_1_ok(self):
        """pk=1 ne lève pas d'erreur."""
        obj = MagicMock(spec=SiteConfiguration)
        obj.pk = 1
        SiteConfiguration.clean(obj)  # ne doit pas lever

    def test_clean_pk_2_raises(self):
        """Pk != 1 lève ValidationError."""
        obj = MagicMock(spec=SiteConfiguration)
        obj.pk = 2
        import pytest

        with pytest.raises(ValidationError):
            SiteConfiguration.clean(obj)

    def test_clean_pk_none_ok(self):
        """pk=None (nouvelle instance) ne lève pas d'erreur."""
        obj = MagicMock(spec=SiteConfiguration)
        obj.pk = None
        SiteConfiguration.clean(obj)  # ne doit pas lever

    # ── delete: empêchée ────────────────────────────────────────────

    def test_delete_does_nothing(self):
        """delete() est un no-op pour le singleton."""
        obj = MagicMock(spec=SiteConfiguration)
        result = SiteConfiguration.delete(obj)
        assert result is None

    # ── get_solo: cache hit ─────────────────────────────────────────

    def test_get_solo_cache_hit(self):
        """Retourne l'objet en cache sans requête DB."""
        cached_obj = MagicMock(spec=SiteConfiguration)
        with patch("django.core.cache.cache") as mock_cache:
            mock_cache.get.return_value = cached_obj
            result = SiteConfiguration.get_solo()
        assert result is cached_obj

    def test_get_solo_cache_miss(self):
        """Cache miss → get_or_create → set en cache."""
        db_obj = MagicMock(spec=SiteConfiguration)
        with (
            patch("django.core.cache.cache") as mock_cache,
            patch.object(
                SiteConfiguration.objects, "get_or_create", return_value=(db_obj, True)
            ),
        ):
            mock_cache.get.return_value = None
            result = SiteConfiguration.get_solo()
        assert result is db_obj
        mock_cache.set.assert_called_once_with("site_configuration_solo", db_obj, 300)

    # ── save: force pk=1 + clear cache ──────────────────────────────

    def test_save_forces_pk_1(self):
        """save() force pk=1 et invalide le cache."""
        obj = SiteConfiguration.__new__(SiteConfiguration)
        obj.pk = 99
        with (
            patch("django.core.cache.cache") as mock_cache,
            patch("django.db.models.Model.save") as mock_super_save,
        ):
            SiteConfiguration.save(obj)
        assert obj.pk == 1
        mock_super_save.assert_called_once()
        mock_cache.delete.assert_called_once_with("site_configuration_solo")

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_maintenance_on(self):
        obj = MagicMock(spec=SiteConfiguration)
        obj.maintenance_mode = True
        obj.banner_enabled = False
        result = SiteConfiguration.__str__(obj)
        assert "MAINTENANCE" in result

    def test_str_maintenance_off(self):
        obj = MagicMock(spec=SiteConfiguration)
        obj.maintenance_mode = False
        obj.banner_enabled = False
        result = SiteConfiguration.__str__(obj)
        assert "En ligne" in result

    def test_str_banner_active(self):
        obj = MagicMock(spec=SiteConfiguration)
        obj.maintenance_mode = False
        obj.banner_enabled = True
        result = SiteConfiguration.__str__(obj)
        assert "Bandeau" in result
