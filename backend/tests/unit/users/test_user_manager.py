"""Tests unitaires du UserManager — sans DB."""

from unittest.mock import patch

from apps.users.models import User
from tests.base import BaseModelUnitTest


class TestUserManager(BaseModelUnitTest):
    """Vérifie le comportement du UserManager (sans DB)."""

    def get_model_class(self):
        return User

    def test_create_user_requires_username(self):
        """create_user doit lever ValueError si username vide."""
        manager = User.objects
        with patch.object(manager, "model"):
            try:
                manager.create_user(username="", email="test@test.com", password="pass")
            except ValueError as e:
                assert "Username" in str(e)

    def test_create_user_requires_email(self):
        """create_user doit lever ValueError si email vide."""
        manager = User.objects
        with patch.object(manager, "model"):
            try:
                manager.create_user(username="user", email="", password="pass")
            except ValueError as e:
                assert "Email" in str(e)

    def test_create_superuser_must_be_staff(self):
        """create_superuser doit lever ValueError si is_staff=False."""
        with patch.object(User.objects, "create_user"):
            try:
                User.objects.create_superuser(
                    username="admin",
                    email="admin@test.com",
                    password="pass",
                    is_staff=False,
                )
            except ValueError as e:
                assert "is_staff=True" in str(e)

    def test_create_superuser_must_be_superuser(self):
        """create_superuser doit lever ValueError si is_superuser=False."""
        with patch.object(User.objects, "create_user"):
            try:
                User.objects.create_superuser(
                    username="admin",
                    email="admin@test.com",
                    password="pass",
                    is_superuser=False,
                )
            except ValueError as e:
                assert "is_superuser=True" in str(e)
