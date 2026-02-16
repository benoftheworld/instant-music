"""
Views for Spotify OAuth 2.0 authentication.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import redirect
from django.conf import settings

from .oauth import spotify_oauth_service, SpotifyOAuthError
from .models import SpotifyToken
from .serializers import SpotifyTokenSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Get Spotify authorization URL",
    description="Returns URL to redirect user to Spotify for authorization",
    responses={
        200: OpenApiResponse(
            description="Authorization URL generated",
            response={
                "type": "object",
                "properties": {
                    "authorization_url": {"type": "string"},
                    "state": {"type": "string"}
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_authorize(request):
    """
    Generate Spotify authorization URL for OAuth flow.
    
    Returns URL that frontend should redirect user to for Spotify login.
    """
    try:
        auth_data = spotify_oauth_service.get_authorization_url(user_id=request.user.id)
        
        return Response({
            'authorization_url': auth_data['url'],
            'state': auth_data['state']
        }, status=status.HTTP_200_OK)
    
    except SpotifyOAuthError as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Spotify OAuth callback",
    description="Handles callback from Spotify after user authorization",
    parameters=[
        {'name': 'code', 'in': 'query', 'required': True, 'schema': {'type': 'string'}},
        {'name': 'state', 'in': 'query', 'required': True, 'schema': {'type': 'string'}},
        {'name': 'error', 'in': 'query', 'required': False, 'schema': {'type': 'string'}},
    ],
    responses={
        302: OpenApiResponse(description="Redirect to frontend"),
    }
)
@api_view(['GET'])
@permission_classes([])  # Allow unauthenticated access for OAuth callback
def spotify_callback(request):
    """
    Handle OAuth callback from Spotify.
    
    This endpoint receives authorization code from Spotify and exchanges it
    for access/refresh tokens. Then redirects user back to frontend.
    
    Query params:
    - code: Authorization code (on success)
    - state: State parameter for CSRF protection
    - error: Error code (if user denied access)
    """
    # Check for authorization error
    error = request.query_params.get('error')
    if error:
        logger.warning(f"User denied Spotify authorization: {error}")
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_error=access_denied"
        return redirect(frontend_url)
    
    # Get code and state
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    
    if not code or not state:
        logger.error("Missing code or state in callback")
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_error=invalid_callback"
        return redirect(frontend_url)
    
    # Validate state (CSRF protection) and get user_id
    user_id = spotify_oauth_service.validate_state(state)
    if not user_id:
        logger.error(f"Invalid or expired state parameter: {state}")
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_error=invalid_state"
        return redirect(frontend_url)
    
    try:
        # Get user from database
        from apps.users.models import User
        user = User.objects.get(id=user_id)
        
        # Exchange code for tokens
        token_data = spotify_oauth_service.exchange_code_for_token(code)
        
        # Save tokens for user
        spotify_oauth_service.save_token_for_user(user, token_data)
        
        logger.info(f"Successfully connected Spotify for user {user.username}")
        
        # Redirect back to frontend with success
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_connected=true"
        return redirect(frontend_url)
    
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_error=user_not_found"
        return redirect(frontend_url)
    
    except SpotifyOAuthError as e:
        logger.error(f"Failed to complete OAuth flow: {e}")
        frontend_url = f"{settings.FRONTEND_URL}/profile?spotify_error=token_exchange_failed"
        return redirect(frontend_url)


@extend_schema(
    summary="Get Spotify connection status",
    description="Check if current user has connected Spotify account",
    responses={
        200: SpotifyTokenSerializer,
        404: OpenApiResponse(description="Not connected")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_status(request):
    """
    Get Spotify connection status for current user.
    
    Returns token info if connected, 404 if not.
    """
    try:
        token = SpotifyToken.objects.get(user=request.user)
        serializer = SpotifyTokenSerializer(token)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except SpotifyToken.DoesNotExist:
        return Response(
            {'connected': False, 'message': 'Spotify not connected'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    summary="Disconnect Spotify",
    description="Revoke Spotify access for current user",
    responses={
        200: OpenApiResponse(description="Successfully disconnected"),
        404: OpenApiResponse(description="Not connected")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spotify_disconnect(request):
    """
    Disconnect Spotify account for current user.
    
    Deletes stored tokens.
    """
    success = spotify_oauth_service.revoke_token_for_user(request.user)
    
    if success:
        return Response(
            {'message': 'Spotify account disconnected successfully'},
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {'message': 'No Spotify account was connected'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    summary="Refresh Spotify token",
    description="Manually refresh access token (usually done automatically)",
    responses={
        200: SpotifyTokenSerializer,
        404: OpenApiResponse(description="Not connected"),
        500: OpenApiResponse(description="Refresh failed")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spotify_refresh(request):
    """
    Manually refresh Spotify access token.
    
    This is usually done automatically, but can be triggered manually.
    """
    try:
        token = SpotifyToken.objects.get(user=request.user)
    except SpotifyToken.DoesNotExist:
        return Response(
            {'error': 'Spotify not connected'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Refresh token
        new_token_data = spotify_oauth_service.refresh_access_token(token.refresh_token)
        updated_token = spotify_oauth_service.save_token_for_user(request.user, new_token_data)
        
        serializer = SpotifyTokenSerializer(updated_token)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except SpotifyOAuthError as e:
        logger.error(f"Failed to refresh token: {e}")
        return Response(
            {'error': 'Failed to refresh token. Please reconnect Spotify.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
