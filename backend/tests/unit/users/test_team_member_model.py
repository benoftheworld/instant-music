"""Tests unitaires du modèle TeamMember — introspection des champs."""

from unittest.mock import MagicMock

from apps.users.models import TeamMember
from apps.users.models.enums import TeamMemberRole
from tests.base import BaseModelUnitTest


class TestTeamMemberModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle TeamMember."""

    def get_model_class(self):
        return TeamMember

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ role ──────────────────────────────────────────────────

    def test_role_max_length(self):
        self.assert_field_max_length(TeamMember, "role", 20)

    def test_role_choices(self):
        self.assert_field_choices(TeamMember, "role", TeamMemberRole.choices)

    def test_role_default(self):
        self.assert_field_default(TeamMember, "role", TeamMemberRole.MEMBER)

    def test_role_values(self):
        """Vérifie les 3 valeurs possibles du rôle."""
        assert TeamMemberRole.OWNER == "owner"
        assert TeamMemberRole.ADMIN == "admin"
        assert TeamMemberRole.MEMBER == "member"

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_team_field_exists(self):
        self.assert_field_exists(TeamMember, "team")

    def test_user_field_exists(self):
        self.assert_field_exists(TeamMember, "user")

    def test_team_cascade(self):
        field = TeamMember._meta.get_field("team")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_user_cascade(self):
        field = TeamMember._meta.get_field("user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Timestamps ──────────────────────────────────────────────────

    def test_joined_at_auto_now_add(self):
        field = TeamMember._meta.get_field("joined_at")
        assert field.auto_now_add is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("membre d'équipe", "membres d'équipe")

    def test_unique_together(self):
        self.assert_unique_together(TeamMember, ["team", "user"])

    def test_ordering(self):
        self.assert_ordering(TeamMember, ["joined_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_team = MagicMock()
        mock_team.name = "Team A"
        member = MagicMock(spec=TeamMember)
        member.user = mock_user
        member.team = mock_team
        result = TeamMember.__str__(member)
        assert "alice" in result
        assert "Team A" in result
