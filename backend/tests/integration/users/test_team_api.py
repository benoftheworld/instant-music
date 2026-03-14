"""Tests d'intégration de l'API Teams."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestTeamCreate(BaseAPIIntegrationTest):
    """Vérifie la création d'équipe."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_create_team_success(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(), {"name": "Team Alpha"}, format="json"
        )
        self.assert_status(resp, 201)
        assert resp.data["name"] == "Team Alpha"

    def test_create_team_unauthenticated(self):
        client = self.get_client()
        resp = client.post(
            self.get_base_url(), {"name": "Team Beta"}, format="json"
        )
        self.assert_status(resp, 401)


class TestTeamList(BaseAPIIntegrationTest):
    """Vérifie la liste des équipes de l'utilisateur."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_list_my_teams(self):
        from apps.users.models import Team, TeamMember, TeamMemberRole

        user = UserFactory()
        team = Team.objects.create(name="My Team", owner=user)
        TeamMember.objects.create(team=team, user=user, role=TeamMemberRole.OWNER)
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert len(resp.data) == 1

    def test_list_empty(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp.data == []


class TestTeamBrowse(BaseAPIIntegrationTest):
    """Vérifie le parcours des équipes publiques."""

    def get_base_url(self):
        return "/api/users/teams/browse/"

    def test_browse_teams(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)


class TestTeamJoin(BaseAPIIntegrationTest):
    """Vérifie la demande d'adhésion à une équipe."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_join_team(self):
        from apps.users.models import Team, TeamMember, TeamMemberRole

        owner = UserFactory()
        team = Team.objects.create(name="Open Team", owner=owner)
        TeamMember.objects.create(team=team, user=owner, role=TeamMemberRole.OWNER)

        joiner = UserFactory()
        client = self.get_auth_client(joiner)
        resp = client.post(f"{self.get_base_url()}{team.id}/join/")
        self.assert_status(resp, 201)

    def test_join_nonexistent_team(self):
        import uuid

        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(f"{self.get_base_url()}{uuid.uuid4()}/join/")
        self.assert_status(resp, 404)


class TestTeamLeave(BaseAPIIntegrationTest):
    """Vérifie le départ d'une équipe."""

    def get_base_url(self):
        return "/api/users/teams/"

    def test_leave_team(self):
        from apps.users.models import Team, TeamMember, TeamMemberRole

        owner = UserFactory()
        member = UserFactory()
        team = Team.objects.create(name="Leave Team", owner=owner)
        TeamMember.objects.create(team=team, user=owner, role=TeamMemberRole.OWNER)
        TeamMember.objects.create(team=team, user=member, role=TeamMemberRole.MEMBER)

        client = self.get_auth_client(member)
        resp = client.post(f"{self.get_base_url()}{team.id}/leave/")
        self.assert_status(resp, 200)

    def test_leave_not_member(self):
        from apps.users.models import Team, TeamMember, TeamMemberRole

        owner = UserFactory()
        team = Team.objects.create(name="Not Member", owner=owner)
        TeamMember.objects.create(team=team, user=owner, role=TeamMemberRole.OWNER)

        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(f"{self.get_base_url()}{team.id}/leave/")
        self.assert_status(resp, 404)
