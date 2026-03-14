"""Tests d'intégration du TeamViewSet."""

import pytest
from rest_framework import status

from apps.users.models import Team, TeamMember, TeamMemberRole
from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestTeamCreate(BaseAPIIntegrationTest):
    """Vérifie la création d'équipe."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_create_team(self, auth_client, user):
        resp = auth_client.post(
            self.get_base_url(),
            {"name": "My Team", "description": "A test team"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert resp.data["name"] == "My Team"
        assert Team.objects.filter(name="My Team").exists()

    def test_create_team_unauthenticated(self, api_client):
        resp = api_client.post(
            self.get_base_url(), {"name": "Team"}, format="json"
        )
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestTeamList(BaseAPIIntegrationTest):
    """Vérifie la liste des équipes."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_list_my_teams(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team1")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) >= 1

    def test_browse_all_teams(self, auth_client, user):
        Team.objects.create(owner=user, name="Team Browse")
        resp = auth_client.get(f"{self.get_base_url()}browse/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestTeamJoin(BaseAPIIntegrationTest):
    """Vérifie la demande d'adhésion."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_join_team(self, auth_client2, user, user2):
        team = Team.objects.create(owner=user, name="Team Join")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client2.post(f"{self.get_base_url()}{team.id}/join/")
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_join_nonexistent_team(self, auth_client):
        import uuid
        resp = auth_client.post(f"{self.get_base_url()}{uuid.uuid4()}/join/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_join_team_duplicate(self, auth_client2, user, user2):
        team = Team.objects.create(owner=user, name="Team Dup")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        auth_client2.post(f"{self.get_base_url()}{team.id}/join/")
        resp = auth_client2.post(f"{self.get_base_url()}{team.id}/join/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestTeamApproveReject(BaseAPIIntegrationTest):
    """Vérifie l'approbation et le rejet des demandes."""

    def get_base_url(self):
        return "/api/users/teams/"

    def _setup_team_with_request(self, user, user2, auth_client2):
        team = Team.objects.create(owner=user, name="Team AR")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        auth_client2.post(f"{self.get_base_url()}{team.id}/join/")
        from apps.users.models import TeamJoinRequest
        jr = TeamJoinRequest.objects.filter(team=team, user=user2).first()
        return team, jr

    def test_approve_request(self, auth_client, auth_client2, user, user2):
        team, jr = self._setup_team_with_request(user, user2, auth_client2)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/approve/",
            {"request_id": str(jr.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_reject_request(self, auth_client, auth_client2, user, user2):
        team, jr = self._setup_team_with_request(user, user2, auth_client2)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/reject/",
            {"request_id": str(jr.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_approve_no_request_id(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team NR")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/approve/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_pending_requests(self, auth_client, user):
        resp = auth_client.get(f"{self.get_base_url()}my_pending_requests/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_list_requests(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team LR")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.get(f"{self.get_base_url()}{team.id}/requests/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestTeamManage(BaseAPIIntegrationTest):
    """Vérifie les actions de gestion d'équipe."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_dissolve_team(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Dissolve")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(f"{self.get_base_url()}{team.id}/dissolve/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert not Team.objects.filter(id=team.id).exists()

    def test_dissolve_team_non_owner(self, auth_client2, user, user2):
        team = Team.objects.create(owner=user, name="Team Dissolve2")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        TeamMember.objects.create(team=team, user=user2, role=TeamMemberRole.MEMBER)
        resp = auth_client2.post(f"{self.get_base_url()}{team.id}/dissolve/")
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)

    def test_leave_team(self, auth_client2, user, user2):
        team = Team.objects.create(owner=user, name="Team Leave")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        TeamMember.objects.create(team=team, user=user2, role=TeamMemberRole.MEMBER)
        resp = auth_client2.post(f"{self.get_base_url()}{team.id}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leave_team_owner_transfers_ownership(self, auth_client, user, user2):
        team = Team.objects.create(owner=user, name="Team Owner Leave")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        TeamMember.objects.create(team=team, user=user2, role=TeamMemberRole.MEMBER)
        resp = auth_client.post(f"{self.get_base_url()}{team.id}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leave_team_sole_owner_deletes(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Sole")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(f"{self.get_base_url()}{team.id}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert not Team.objects.filter(id=team.id).exists()

    def test_edit_team(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Edit")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.patch(
            f"{self.get_base_url()}{team.id}/edit/",
            {"description": "Updated description"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_invite_member(self, auth_client, user, user2):
        team = Team.objects.create(owner=user, name="Team Invite")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/invite/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_invite_nonexistent_user(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Invite NE")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/invite/",
            {"username": "nonexistent_xyz"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_invite_no_username(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Invite No")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/invite/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestTeamRolesAndMembers(BaseAPIIntegrationTest):
    """Vérifie la gestion des rôles et suppression de membres."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_update_member_role(self, auth_client, user, user2):
        team = Team.objects.create(owner=user, name="Team Roles")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        member = TeamMember.objects.create(
            team=team, user=user2, role=TeamMemberRole.MEMBER
        )
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/update_member/",
            {"member_id": str(member.id), "role": TeamMemberRole.ADMIN},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_update_member_missing_params(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Roles2")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/update_member/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_remove_member(self, auth_client, user, user2):
        team = Team.objects.create(owner=user, name="Team Remove")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        member = TeamMember.objects.create(
            team=team, user=user2, role=TeamMemberRole.MEMBER
        )
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/remove_member/",
            {"member_id": str(member.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_remove_member_no_id(self, auth_client, user):
        team = Team.objects.create(owner=user, name="Team Remove2")
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/remove_member/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_remove_owner_fails(self, auth_client, user, user2):
        team = Team.objects.create(owner=user, name="Team Remove Owner")
        owner_member = TeamMember.objects.create(
            team=team, user=user, role=TeamMemberRole.OWNER
        )
        TeamMember.objects.create(team=team, user=user2, role=TeamMemberRole.ADMIN)
        resp = auth_client.post(
            f"{self.get_base_url()}{team.id}/remove_member/",
            {"member_id": str(owner_member.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
