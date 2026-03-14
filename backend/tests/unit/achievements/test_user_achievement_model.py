"""Tests unitaires du modèle UserAchievement."""

from unittest.mock import MagicMock

from apps.achievements.models import UserAchievement
from tests.base import BaseModelUnitTest


class TestUserAchievementModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle UserAchievement."""

    def get_model_class(self):
        return UserAchievement

    # ── PK ──────────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── FK ──────────────────────────────────────────────────────────

    def test_user_cascade(self):
        field = UserAchievement._meta.get_field("user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_achievement_cascade(self):
        field = UserAchievement._meta.get_field("achievement")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Timestamps ──────────────────────────────────────────────────

    def test_unlocked_at_auto_now_add(self):
        field = UserAchievement._meta.get_field("unlocked_at")
        assert field.auto_now_add is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_unique_together(self):
        self.assert_unique_together(UserAchievement, ["user", "achievement"])

    def test_verbose_name(self):
        self.assert_meta_verbose_name("succès utilisateur", "succès utilisateurs")

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_achievement = MagicMock()
        mock_achievement.name = "Premier pas"
        ua = MagicMock(spec=UserAchievement)
        ua.user = mock_user
        ua.achievement = mock_achievement
        result = UserAchievement.__str__(ua)
        assert "alice" in result
        assert "Premier pas" in result
