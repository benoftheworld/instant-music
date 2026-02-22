"""ViewSet for User model."""

from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import User
from ..serializers import (
    ChangePasswordSerializer,
    UserMinimalSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user."""
        if self.action == "list":
            if self.request.user.is_staff:
                return User.objects.all()
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == "GET":
            serializer = UserSerializer(
                request.user, context={"request": request}
            )
            return Response(serializer.data)

        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(
                    request.user, context={"request": request}
                ).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user

            if not user.check_password(
                serializer.validated_data["old_password"]
            ):
                return Response(
                    {"old_password": "Mot de passe incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()
            update_session_auth_hash(request, user)

            return Response(
                {"message": "Mot de passe modifié avec succès."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["delete"])
    def delete_account(self, request):
        """Delete user account and all associated data (GDPR)."""
        with transaction.atomic():
            request.user.delete()

        return Response(
            {"message": "Compte supprimé avec succès."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search users by username."""
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])

        users = (
            User.objects.filter(username__icontains=query)
            .exclude(id=request.user.id)[:10]
        )

        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data)
