"""Tests d'intégration étendus — couverture des branches manquantes friendship_viewset."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status

from apps.users.models import Friendship, FriendshipStatus
from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory

BASE = "/api/users/friends/"


@pytest.mark.django_db
class TestFriendshipListSuperuserExcluded(BaseAPIIntegrationTest):
    """Line 41 — superuser friends are excluded from the list."""

    def get_base_url(self):
        return BASE

    def test_superuser_friend_is_excluded(self, auth_client, user):
        su = UserFactory(is_superuser=True)
        Friendship.objects.create(
            from_user=user, to_user=su, status=FriendshipStatus.ACCEPTED
        )
        resp = auth_client.get(BASE)
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) == 0

    def test_mixed_friends_excludes_only_superuser(self, auth_client, user, user2):
        su = UserFactory(is_superuser=True)
        Friendship.objects.create(
            from_user=user, to_user=su, status=FriendshipStatus.ACCEPTED
        )
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.ACCEPTED
        )
        resp = auth_client.get(BASE)
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) == 1


@pytest.mark.django_db
class TestFriendshipSendRequestWsException(BaseAPIIntegrationTest):
    """Lines 126-127, 152-153 — WS notification exceptions on send_request."""

    def get_base_url(self):
        return BASE

    @patch("apps.users.views.friendship_viewset.get_channel_layer")
    def test_reuse_rejected_ws_exception(self, mock_cl, auth_client, user, user2):
        """WS exception when re-sending after rejection (lines 126-127)."""
        Friendship.objects.create(
            from_user=user, to_user=user2, status=FriendshipStatus.REJECTED
        )
        mock_cl.return_value.group_send = MagicMock(side_effect=Exception("WS fail"))
        # async_to_sync wraps group_send; we patch at channel layer level
        with patch(
            "apps.users.views.friendship_viewset.async_to_sync"
        ) as mock_ats:
            mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
            resp = auth_client.post(
                f"{BASE}send_request/",
                {"username": user2.username},
                format="json",
            )
        self.assert_status(resp, status.HTTP_201_CREATED)

    @patch("apps.users.views.friendship_viewset.async_to_sync")
    def test_new_request_ws_exception(self, mock_ats, auth_client, user, user2):
        """WS exception on new friend request (lines 152-153)."""
        mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
        resp = auth_client.post(
            f"{BASE}send_request/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)


@pytest.mark.django_db
class TestFriendshipAcceptWsException(BaseAPIIntegrationTest):
    """Lines 185-186 — WS notification + achievement exception on accept."""

    def get_base_url(self):
        return BASE

    @patch("apps.users.views.friendship_viewset.async_to_sync")
    def test_accept_ws_exception(self, mock_ats, auth_client, user, user2):
        f = Friendship.objects.create(
            from_user=user2, to_user=user, status=FriendshipStatus.PENDING
        )
        mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
        resp = auth_client.post(f"{BASE}{f.id}/accept/")
        self.assert_status(resp, status.HTTP_200_OK)
        f.refresh_from_db()
        assert f.status == FriendshipStatus.ACCEPTED

    @patch("apps.achievements.services.achievement_service.check_and_award")
    def test_accept_achievement_exception(self, mock_award, auth_client, user, user2):
        f = Friendship.objects.create(
            from_user=user2, to_user=user, status=FriendshipStatus.PENDING
        )
        mock_award.side_effect = Exception("Achievement fail")
        resp = auth_client.post(f"{BASE}{f.id}/accept/")
        self.assert_status(resp, status.HTTP_200_OK)
        f.refresh_from_db()
        assert f.status == FriendshipStatus.ACCEPTED
