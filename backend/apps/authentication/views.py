"""Views for authentication."""

import logging
from base64 import urlsafe_b64decode, urlsafe_b64encode

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core.throttles import (
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
    TokenRefreshThrottle,
)
from apps.users.encryption import hash_email
from apps.users.serializers import UserSerializer

from .cookies import (
    clear_refresh_cookie,
    get_refresh_from_cookie,
    set_refresh_cookie,
)
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()

_token_generator = PasswordResetTokenGenerator()


class ThrottledTokenRefreshView(TokenRefreshView):
    """Token refresh avec rate limiting.

    Lit le refresh token depuis le cookie HttpOnly (et non depuis le body).
    Retourne un nouvel access token dans le JSON et un nouveau refresh en cookie.
    """

    throttle_classes = [TokenRefreshThrottle]

    def post(self, request, *args, **kwargs):
        """Handle token refresh using the HttpOnly refresh cookie."""
        # Injecte le refresh token du cookie dans request.data pour que
        # simplejwt le traite normalement via son serializer.
        refresh = get_refresh_from_cookie(request)
        if not refresh:
            return Response(
                {"error": "Refresh token manquant."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        request._full_data = {"refresh": refresh}  # noqa: SLF001
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Stocker le nouveau refresh token en cookie
            new_refresh = response.data.get("refresh")
            if new_refresh:
                set_refresh_cookie(response, new_refresh)
                del response.data["refresh"]

        return response


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    """Blackliste le refresh token (lu depuis le cookie) et supprime le cookie."""
    refresh_token = get_refresh_from_cookie(request)
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)  # type: ignore[arg-type]
            token.blacklist()
        except TokenError:
            pass  # Token déjà invalide ou expiré
    response = Response(status=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register(request):
    """Register a new user."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    logger.info(
        "user_registered",
        extra={"user_id": user.id, "username": user.username},
    )

    response = Response(
        {
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
            },
        },
        status=status.HTTP_201_CREATED,
    )
    set_refresh_cookie(response, str(refresh))
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    """Login user."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    identifier = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    # Permettre la connexion par email : si l'identifiant contient '@',
    # on résout d'abord l'email en nom d'utilisateur.
    username = identifier
    if "@" in identifier:
        try:
            target_user = User.objects.get(email_hash=hash_email(identifier))
            username = target_user.username
        except User.DoesNotExist:
            logger.warning(
                "login_email_not_found",
                extra={"identifier_type": "email"},
            )
            return Response(
                {"error": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    user = authenticate(username=username, password=password)

    if user is not None:
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Bonus connexion quotidienne : +2 pièces par jour
        import datetime

        from django.db.models import F as _F

        today = datetime.date.today()
        if user.last_daily_login != today:
            user.__class__.objects.filter(pk=user.pk).update(
                last_daily_login=today,
                coins_balance=_F("coins_balance") + 2,
            )
            user.refresh_from_db()

        response = Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                },
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response

    logger.warning(
        "login_failed",
        extra={"username": username},
    )
    return Response(
        {"error": "Identifiants invalides."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_request(request):
    """Demande de réinitialisation de mot de passe.

    Envoie un email avec un lien de réinitialisation si le pseudonyme ou l'email existe.
    Retourne toujours 200 pour éviter l'énumération de comptes.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = serializer.validated_data["identifier"]
    success_response = Response(
        {"message": "Si ce compte existe, un lien de réinitialisation a été envoyé."},
        status=status.HTTP_200_OK,
    )

    # Résolution par email (si '@') ou par pseudonyme
    try:
        if "@" in identifier:
            user = User.objects.get(email_hash=hash_email(identifier))
        else:
            user = User.objects.get(username=identifier)
    except User.DoesNotExist:
        return success_response

    if not user.is_active:
        return success_response

    # Génération du token et de l'UID (base64 de l'UUID)
    uid = urlsafe_b64encode(str(user.pk).encode()).decode()
    token = _token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    # Envoi de l'email (console en dev, SMTP en prod)
    try:
        message = (
            f"Bonjour {user.username},\n\n"
            f"Vous avez demandé à réinitialiser votre mot de passe.\n"
            f"Cliquez sur le lien suivant (valable 1h) :\n\n"
            f"{reset_url}\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n\n"
            f"L'équipe InstantMusic"
        )
        send_mail(
            subject="Réinitialisation de votre mot de passe InstantMusic",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Échec de l'envoi de l'email de réinitialisation pour %s", user.pk
        )
        # Ne pas exposer l'erreur à l'utilisateur

    return success_response


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_confirm(request):
    """Confirm password reset.

    Valide le token reçu par email et met à jour le mot de passe.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]
    new_password = serializer.validated_data["new_password"]

    # Décoder l'UID (base64 de l'UUID utilisateur)
    try:
        user_pk = urlsafe_b64decode(uid.encode()).decode()
        user = User.objects.get(pk=user_pk)
    except (Exception, User.DoesNotExist):
        return Response(
            {"error": "Lien invalide ou expiré."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Valider le token (expire après 1h par défaut via PASSWORD_RESET_TIMEOUT)
    if not _token_generator.check_token(user, token):
        return Response(
            {"error": "Lien invalide ou expiré."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save(update_fields=["password"])

    logger.info("Mot de passe réinitialisé pour l'utilisateur %s", user.pk)

    return Response(
        {"message": "Mot de passe réinitialisé avec succès."},
        status=status.HTTP_200_OK,
    )
