"""Tests unitaires du modèle TeamJoinRequest — introspection des champs."""

from unittest.mock import MagicMock

from apps.users.models import TeamJoinRequest
from apps.users.models.enums import TeamJoinRequestStatus
from tests.base import BaseModelUnitTest


class TestTeamJoinRequestModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle TeamJoinRequest."""

    def get_model_class(self):
        return TeamJoinRequest

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ status ────────────────────────────────────────────────

    def test_status_max_length(self):
        self.assert_field_max_length(TeamJoinRequest, "status", 20)

    def test_status_choices(self):
        self.assert_field_choices(
            TeamJoinRequest, "status", TeamJoinRequestStatus.choices
        )

    def test_status_default(self):
        self.assert_field_default(
            TeamJoinRequest, "status", TeamJoinRequestStatus.PENDING
        )

    def test_status_db_index(self):
        self.assert_field_db_index(TeamJoinRequest, "status", True)

    def test_status_values(self):
        """Vérifie les 3 valeurs possibles."""
        assert TeamJoinRequestStatus.PENDING == "pending"
        assert TeamJoinRequestStatus.APPROVED == "approved"
        assert TeamJoinRequestStatus.REJECTED == "rejected"

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_team_field_exists(self):
        self.assert_field_exists(TeamJoinRequest, "team")

    def test_user_field_exists(self):
        self.assert_field_exists(TeamJoinRequest, "user")

    def test_team_cascade(self):
        field = TeamJoinRequest._meta.get_field("team")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_user_cascade(self):
        field = TeamJoinRequest._meta.get_field("user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = TeamJoinRequest._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_updated_at_auto_now(self):
        field = TeamJoinRequest._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("demande d'adhésion", "demandes d'adhésion")

    def test_unique_together(self):
        self.assert_unique_together(TeamJoinRequest, ["team", "user"])

    def test_ordering(self):
        self.assert_ordering(TeamJoinRequest, ["-created_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "bob"
        mock_team = MagicMock()
        mock_team.name = "Team X"
        request = MagicMock(spec=TeamJoinRequest)
        request.user = mock_user
        request.team = mock_team
        request.status = "pending"
        result = TeamJoinRequest.__str__(request)
        assert "bob" in result
        assert "Team X" in result
        assert "pending" in result
