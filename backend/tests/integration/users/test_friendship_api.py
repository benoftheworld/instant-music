"""Tests d'intégration de l'API Friendship."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestFriendshipSendRequest(BaseAPIIntegrationTest):
    """Vérifie l'envoi de demandes d'ami."""

    def get_base_url(self):
        return "/api/users/friends/send_request/"

    def test_send_request_success(self):
        user = UserFactory()
        target = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(), {"username": target.username}, format="json"
        )
        self.assert_status(resp, 201)
        assert resp.data["status"] == "pending"

    def test_send_request_to_self(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(), {"username": user.username}, format="json"
        )
        self.assert_status(resp, 400)

    def test_send_request_unauthenticated(self):
        target = UserFactory()
        client = self.get_client()
        resp = client.post(
            self.get_base_url(), {"username": target.username}, format="json"
        )
        self.assert_status(resp, 401)


class TestFriendshipAcceptReject(BaseAPIIntegrationTest):
    """Vérifie l'acceptation et le refus de demandes."""

    def get_base_url(self):
        return "/api/users/friends/"

    def _create_pending_request(self):
        from apps.users.models import Friendship, FriendshipStatus

        sender = UserFactory()
        receiver = UserFactory()
        friendship = Friendship.objects.create(
            from_user=sender,
            to_user=receiver,
            status=FriendshipStatus.PENDING,
        )
        return sender, receiver, friendship

    def test_accept_request(self):
        sender, receiver, friendship = self._create_pending_request()
        client = self.get_auth_client(receiver)
        resp = client.post(f"{self.get_base_url()}{friendship.id}/accept/")
        self.assert_status(resp, 200)

    def test_reject_request(self):
        sender, receiver, friendship = self._create_pending_request()
        client = self.get_auth_client(receiver)
        resp = client.post(f"{self.get_base_url()}{friendship.id}/reject/")
        self.assert_status(resp, 200)

    def test_accept_nonexistent(self):
        import uuid

        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(f"{self.get_base_url()}{uuid.uuid4()}/accept/")
        self.assert_status(resp, 404)


class TestFriendshipList(BaseAPIIntegrationTest):
    """Vérifie la liste des amis."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_list_friends_empty(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp.data == []

    def test_list_friends_with_accepted(self):
        from apps.users.models import Friendship, FriendshipStatus

        user = UserFactory()
        friend = UserFactory()
        Friendship.objects.create(
            from_user=user, to_user=friend, status=FriendshipStatus.ACCEPTED
        )
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert len(resp.data) == 1


class TestFriendshipRemove(BaseAPIIntegrationTest):
    """Vérifie la suppression d'un ami."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_remove_friend(self):
        from apps.users.models import Friendship, FriendshipStatus

        user = UserFactory()
        friend = UserFactory()
        friendship = Friendship.objects.create(
            from_user=user, to_user=friend, status=FriendshipStatus.ACCEPTED
        )
        client = self.get_auth_client(user)
        resp = client.delete(f"{self.get_base_url()}{friendship.id}/remove/")
        self.assert_status(resp, 200)

    def test_remove_nonexistent(self):
        import uuid

        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.delete(f"{self.get_base_url()}{uuid.uuid4()}/remove/")
        self.assert_status(resp, 404)
