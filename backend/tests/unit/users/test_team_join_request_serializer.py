"""Tests unitaires de TeamJoinRequestCreateSerializer.validate."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestTeamJoinRequestCreateSerializerValidate(BaseUnitTest):
    """Vérifie la validation de la demande d'adhésion."""

    def get_target_class(self):
        from apps.users.serializers.team_serializer import TeamJoinRequestCreateSerializer
        return TeamJoinRequestCreateSerializer

    @patch("apps.users.serializers.team_serializer.TeamJoinRequest")
    @patch("apps.users.serializers.team_serializer.TeamMember")
    def test_valid_request(self, mock_member, mock_jr):
        from apps.users.serializers.team_serializer import TeamJoinRequestCreateSerializer
        mock_member.objects.filter.return_value.exists.return_value = False
        mock_jr.objects.get.side_effect = mock_jr.DoesNotExist
        user = MagicMock()
        team = MagicMock()
        ser = TeamJoinRequestCreateSerializer(
            context={"request": MagicMock(user=user), "team": team}
        )
        result = ser.validate({})
        assert result == {}

    @patch("apps.users.serializers.team_serializer.TeamMember")
    def test_already_member_raises(self, mock_member):
        from rest_framework import serializers as drf_ser
        from apps.users.serializers.team_serializer import TeamJoinRequestCreateSerializer
        mock_member.objects.filter.return_value.exists.return_value = True
        user = MagicMock()
        team = MagicMock()
        ser = TeamJoinRequestCreateSerializer(
            context={"request": MagicMock(user=user), "team": team}
        )
        try:
            ser.validate({})
            assert False, "Expected ValidationError"
        except drf_ser.ValidationError:
            pass

    @patch("apps.users.serializers.team_serializer.TeamJoinRequest")
    @patch("apps.users.serializers.team_serializer.TeamMember")
    def test_pending_request_raises(self, mock_member, mock_jr):
        from rest_framework import serializers as drf_ser
        from apps.users.serializers.team_serializer import (
            TeamJoinRequestCreateSerializer,
            TeamJoinRequestStatus,
        )
        mock_member.objects.filter.return_value.exists.return_value = False
        existing = MagicMock(status=TeamJoinRequestStatus.PENDING)
        mock_jr.objects.get.return_value = existing
        user = MagicMock()
        team = MagicMock()
        ser = TeamJoinRequestCreateSerializer(
            context={"request": MagicMock(user=user), "team": team}
        )
        try:
            ser.validate({})
            assert False, "Expected ValidationError"
        except drf_ser.ValidationError:
            pass

    @patch("apps.users.serializers.team_serializer.TeamJoinRequest")
    @patch("apps.users.serializers.team_serializer.TeamMember")
    def test_rejected_request_allows_new(self, mock_member, mock_jr):
        from apps.users.serializers.team_serializer import (
            TeamJoinRequestCreateSerializer,
            TeamJoinRequestStatus,
        )
        mock_member.objects.filter.return_value.exists.return_value = False
        existing = MagicMock(status=TeamJoinRequestStatus.REJECTED)
        mock_jr.objects.get.return_value = existing
        user = MagicMock()
        team = MagicMock()
        ser = TeamJoinRequestCreateSerializer(
            context={"request": MagicMock(user=user), "team": team}
        )
        result = ser.validate({})
        assert result == {}
