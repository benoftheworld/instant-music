"""Tests unitaires du modèle Friendship — introspection des champs."""

from unittest.mock import MagicMock

from apps.users.models import Friendship
from apps.users.models.enums import FriendshipStatus
from tests.base import BaseModelUnitTest


class TestFriendshipModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle Friendship."""

    def get_model_class(self):
        return Friendship

    # ── PK UUID ─────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ status ────────────────────────────────────────────────

    def test_status_max_length(self):
        self.assert_field_max_length(Friendship, "status", 20)

    def test_status_choices(self):
        self.assert_field_choices(Friendship, "status", FriendshipStatus.choices)

    def test_status_default(self):
        self.assert_field_default(Friendship, "status", FriendshipStatus.PENDING)

    def test_status_db_index(self):
        self.assert_field_db_index(Friendship, "status", True)

    def test_status_values(self):
        """Vérifie les 3 valeurs possibles du statut."""
        assert FriendshipStatus.PENDING == "pending"
        assert FriendshipStatus.ACCEPTED == "accepted"
        assert FriendshipStatus.REJECTED == "rejected"

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_from_user_field_exists(self):
        self.assert_field_exists(Friendship, "from_user")

    def test_to_user_field_exists(self):
        self.assert_field_exists(Friendship, "to_user")

    def test_from_user_cascade(self):
        field = Friendship._meta.get_field("from_user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_to_user_cascade(self):
        field = Friendship._meta.get_field("to_user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = Friendship._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_updated_at_auto_now(self):
        field = Friendship._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("amitié", "amitiés")

    def test_unique_together(self):
        self.assert_unique_together(Friendship, ["from_user", "to_user"])

    def test_ordering(self):
        self.assert_ordering(Friendship, ["-created_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_from = MagicMock()
        mock_from.username = "alice"
        mock_to = MagicMock()
        mock_to.username = "bob"
        friendship = MagicMock(spec=Friendship)
        friendship.from_user = mock_from
        friendship.to_user = mock_to
        friendship.status = "pending"
        result = Friendship.__str__(friendship)
        assert "alice" in result
        assert "bob" in result
        assert "pending" in result
