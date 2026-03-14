"""Permissions personnalisées pour l'app games."""

from rest_framework import permissions


class IsGameHost(permissions.BasePermission):
    """Autorise uniquement l'hôte de la partie."""

    message = "Seul l'hôte peut effectuer cette action."

    def has_object_permission(self, request, view, obj):
        """Check that the requesting user is the game host."""
        return obj.host == request.user
