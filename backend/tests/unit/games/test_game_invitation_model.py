"""Tests unitaires du modèle GameInvitation — introspection et logique."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.utils import timezone

from apps.games.models import GameInvitation
from apps.games.models.game_invitation import INVITATION_TTL_MINUTES, InvitationStatus
from tests.base import BaseModelUnitTest


class TestGameInvitationModel(BaseModelUnitTest):
    """Vérifie les champs, la logique d'expiration et les métadonnées."""

    def get_model_class(self):
        return GameInvitation

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ status ────────────────────────────────────────────────

    def test_status_max_length(self):
        self.assert_field_max_length(GameInvitation, "status", 20)

    def test_status_choices(self):
        self.assert_field_choices(
            GameInvitation, "status", InvitationStatus.choices
        )

    def test_status_default(self):
        self.assert_field_default(GameInvitation, "status", InvitationStatus.PENDING)

    def test_status_db_index(self):
        self.assert_field_db_index(GameInvitation, "status", True)

    def test_invitation_status_values(self):
        """Vérifie les 5 valeurs possibles du statut."""
        assert InvitationStatus.PENDING == "pending"
        assert InvitationStatus.ACCEPTED == "accepted"
        assert InvitationStatus.DECLINED == "declined"
        assert InvitationStatus.EXPIRED == "expired"
        assert InvitationStatus.CANCELLED == "cancelled"

    # ── TTL constant ────────────────────────────────────────────────

    def test_invitation_ttl_is_30_minutes(self):
        assert INVITATION_TTL_MINUTES == 30

    # ── expires_at ──────────────────────────────────────────────────

    def test_expires_at_db_index(self):
        self.assert_field_db_index(GameInvitation, "expires_at", True)

    # ── is_expired property ─────────────────────────────────────────

    def test_is_expired_false_when_future(self):
        invitation = MagicMock(spec=GameInvitation)
        invitation.expires_at = timezone.now() + timedelta(minutes=10)
        result = GameInvitation.is_expired.fget(invitation)
        assert result is False

    def test_is_expired_true_when_past(self):
        invitation = MagicMock(spec=GameInvitation)
        invitation.expires_at = timezone.now() - timedelta(minutes=10)
        result = GameInvitation.is_expired.fget(invitation)
        assert result is True

    def test_is_expired_true_when_exactly_now(self):
        """L'invitation est expirée si timezone.now() > expires_at."""
        now = timezone.now()
        invitation = MagicMock(spec=GameInvitation)
        invitation.expires_at = now - timedelta(seconds=1)
        result = GameInvitation.is_expired.fget(invitation)
        assert result is True

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_game_cascade(self):
        field = GameInvitation._meta.get_field("game")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_sender_cascade(self):
        field = GameInvitation._meta.get_field("sender")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_recipient_cascade(self):
        field = GameInvitation._meta.get_field("recipient")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("invitation de partie", "invitations de partie")

    def test_unique_together(self):
        self.assert_unique_together(GameInvitation, ["game", "recipient"])

    def test_ordering(self):
        self.assert_ordering(GameInvitation, ["-created_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_sender = MagicMock()
        mock_sender.username = "alice"
        mock_recipient = MagicMock()
        mock_recipient.username = "bob"
        mock_game = MagicMock()
        mock_game.room_code = "ABC123"
        invitation = MagicMock(spec=GameInvitation)
        invitation.sender = mock_sender
        invitation.recipient = mock_recipient
        invitation.game = mock_game
        invitation.status = "pending"
        result = GameInvitation.__str__(invitation)
        assert "alice" in result
        assert "bob" in result
        assert "ABC123" in result
