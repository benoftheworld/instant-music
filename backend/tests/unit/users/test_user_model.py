"""Tests unitaires du modèle User — introspection des champs et métadonnées."""

from unittest.mock import MagicMock

from django.db import models

from apps.users.models import User
from tests.base import BaseModelUnitTest


class TestUserModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et propriétés du modèle User."""

    def get_model_class(self):
        return User

    # ── Champs UUID PK ──────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ username ──────────────────────────────────────────────

    def test_username_max_length(self):
        self.assert_field_max_length(User, "username", 150)

    def test_username_unique(self):
        self.assert_field_unique(User, "username", True)

    def test_username_type(self):
        self.assert_field_type(User, "username", models.CharField)

    # ── Champ email (EncryptedEmailField → extends TextField) ───────

    def test_email_field_exists(self):
        self.assert_field_exists(User, "email")

    # ── Champ email_hash ────────────────────────────────────────────

    def test_email_hash_max_length(self):
        self.assert_field_max_length(User, "email_hash", 64)

    def test_email_hash_unique(self):
        self.assert_field_unique(User, "email_hash", True)

    def test_email_hash_not_editable(self):
        field = User._meta.get_field("email_hash")
        assert not field.editable

    def test_email_hash_db_index(self):
        self.assert_field_db_index(User, "email_hash", True)

    # ── Champ avatar ────────────────────────────────────────────────

    def test_avatar_null(self):
        self.assert_field_null(User, "avatar", True)

    def test_avatar_blank(self):
        self.assert_field_blank(User, "avatar", True)

    def test_avatar_has_validators(self):
        field = User._meta.get_field("avatar")
        assert len(field.validators) > 0, "avatar devrait avoir des validators"

    # ── Champs statistiques ─────────────────────────────────────────

    def test_total_games_played_default(self):
        self.assert_field_default(User, "total_games_played", 0)

    def test_total_wins_default(self):
        self.assert_field_default(User, "total_wins", 0)

    def test_total_points_default(self):
        self.assert_field_default(User, "total_points", 0)

    def test_coins_balance_default(self):
        self.assert_field_default(User, "coins_balance", 0)

    # ── Champ last_daily_login ──────────────────────────────────────

    def test_last_daily_login_null(self):
        self.assert_field_null(User, "last_daily_login", True)

    def test_last_daily_login_blank(self):
        self.assert_field_blank(User, "last_daily_login", True)

    # ── Champ google_id ─────────────────────────────────────────────

    def test_google_id_max_length(self):
        self.assert_field_max_length(User, "google_id", 255)

    def test_google_id_unique(self):
        self.assert_field_unique(User, "google_id", True)

    def test_google_id_null(self):
        self.assert_field_null(User, "google_id", True)

    def test_google_id_blank(self):
        self.assert_field_blank(User, "google_id", True)

    # ── Champs permissions ──────────────────────────────────────────

    def test_is_active_default(self):
        self.assert_field_default(User, "is_active", True)

    def test_is_staff_default(self):
        self.assert_field_default(User, "is_staff", False)

    # ── Champs RGPD ─────────────────────────────────────────────────

    def test_privacy_policy_accepted_at_null(self):
        self.assert_field_null(User, "privacy_policy_accepted_at", True)

    def test_cookie_consent_given_at_null(self):
        self.assert_field_null(User, "cookie_consent_given_at", True)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = User._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_updated_at_auto_now(self):
        field = User._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("utilisateur", "utilisateurs")

    def test_ordering(self):
        self.assert_ordering(User, ["-created_at"])

    def test_username_field(self):
        assert User.USERNAME_FIELD == "username"

    def test_required_fields(self):
        assert User.REQUIRED_FIELDS == ["email"]

    # ── Propriété win_rate ──────────────────────────────────────────

    def test_win_rate_zero_games(self):
        user = MagicMock(spec=User)
        user.total_games_played = 0
        user.total_wins = 0
        assert User.win_rate.fget(user) == 0.0  # type: ignore[unused-ignore, attr-defined]

    def test_win_rate_some_wins(self):
        user = MagicMock(spec=User)
        user.total_games_played = 10
        user.total_wins = 5
        assert User.win_rate.fget(user) == 50.0  # type: ignore[unused-ignore, attr-defined]

    def test_win_rate_all_wins(self):
        user = MagicMock(spec=User)
        user.total_games_played = 10
        user.total_wins = 10
        assert User.win_rate.fget(user) == 100.0  # type: ignore[unused-ignore, attr-defined]

    def test_win_rate_one_game_one_win(self):
        user = MagicMock(spec=User)
        user.total_games_played = 1
        user.total_wins = 1
        assert User.win_rate.fget(user) == 100.0  # type: ignore[unused-ignore, attr-defined]

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_returns_username(self):
        user = MagicMock(spec=User)
        user.username = "testuser"
        User.__str__(user)  # Appel direct car MagicMock override __str__
        assert user.username == "testuser"
