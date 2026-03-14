"""Permissions personnalisées pour l'app users."""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Autorise la modification uniquement si l'objet est l'utilisateur lui-même."""

    def has_object_permission(self, request, view, obj):
        """Check that write access is only allowed for the object owner."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user
