"""Tests d'intégration des vues d'amitié."""

import pytest
from rest_framework import status

from apps.users.models import Friendship, FriendshipStatus
from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestFriendshipList(BaseAPIIntegrationTest):
    """Vérifie le listing des amis."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_list_empty(self, auth_client):
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data == []

    def test_list_with_friend(self, auth_client, user, user2):
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.ACCEPTED
        )
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) == 1

    def test_list_unauthenticated(self, api_client):
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestFriendshipPending(BaseAPIIntegrationTest):
    """Vérifie les demandes en attente."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_pending_empty(self, auth_client):
        resp = auth_client.get(f"{self.get_base_url()}pending/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data == []

    def test_pending_with_request(self, auth_client, user, user2):
        Friendship.objects.create(
            from_user=user2, to_user=user, status=FriendshipStatus.PENDING
        )
        resp = auth_client.get(f"{self.get_base_url()}pending/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) == 1

    def test_sent_empty(self, auth_client):
        resp = auth_client.get(f"{self.get_base_url()}sent/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data == []


@pytest.mark.django_db
class TestFriendshipSendRequest(BaseAPIIntegrationTest):
    """Vérifie l'envoi de demandes d'amitié."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_send_request_success(self, auth_client, user2):
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_send_request_to_self(self, auth_client, user):
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": user.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_send_request_already_friends(self, auth_client, user, user2):
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.ACCEPTED
        )
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_send_request_already_pending(self, auth_client, user, user2):
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.PENDING
        )
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_send_request_reuse_rejected(self, auth_client, user, user2):
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.REJECTED
        )
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_send_request_to_superuser(self, auth_client, staff_user):
        # staff_user is is_staff=True but not is_superuser=True
        # so this creates a request normally
        resp = auth_client.post(
            f"{self.get_base_url()}send_request/",
            {"username": staff_user.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)


@pytest.mark.django_db
class TestFriendshipAcceptReject(BaseAPIIntegrationTest):
    """Vérifie l'acceptation et le refus de demandes."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_accept_success(self, auth_client, user, user2):
        f = Friendship.objects.create(
            from_user=user2, to_user=user, status=FriendshipStatus.PENDING
        )
        resp = auth_client.post(f"{self.get_base_url()}{f.id}/accept/")
        self.assert_status(resp, status.HTTP_200_OK)
        f.refresh_from_db()
        assert f.status == FriendshipStatus.ACCEPTED

    def test_accept_not_found(self, auth_client):
        import uuid

        resp = auth_client.post(f"{self.get_base_url()}{uuid.uuid4()}/accept/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_reject_success(self, auth_client, user, user2):
        f = Friendship.objects.create(
            from_user=user2, to_user=user, status=FriendshipStatus.PENDING
        )
        resp = auth_client.post(f"{self.get_base_url()}{f.id}/reject/")
        self.assert_status(resp, status.HTTP_200_OK)
        f.refresh_from_db()
        assert f.status == FriendshipStatus.REJECTED

    def test_reject_not_found(self, auth_client):
        import uuid

        resp = auth_client.post(f"{self.get_base_url()}{uuid.uuid4()}/reject/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestFriendshipRemove(BaseAPIIntegrationTest):
    """Vérifie la suppression d'amitié."""

    def get_base_url(self):
        return "/api/users/friends/"

    def test_remove_success(self, auth_client, user, user2):
        f = Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.ACCEPTED
        )
        resp = auth_client.delete(f"{self.get_base_url()}{f.id}/remove/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert not Friendship.objects.filter(id=f.id).exists()

    def test_remove_not_found(self, auth_client):
        import uuid

        resp = auth_client.delete(f"{self.get_base_url()}{uuid.uuid4()}/remove/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)
