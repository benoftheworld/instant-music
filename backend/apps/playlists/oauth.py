"""
Spotify OAuth 2.0 Authorization Code Flow implementation.
"""
import logging
import secrets
from typing import Dict, Optional
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import SpotifyToken

logger = logging.getLogger(__name__)


class SpotifyOAuthError(Exception):
    """Custom exception for Spotify OAuth errors."""
    pass


class SpotifyOAuthService:
    """Service to handle Spotify OAuth 2.0 Authorization Code Flow."""
    
    AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    
    # Scopes needed for playlist access
    SCOPES = [
        "playlist-read-private",
        "playlist-read-collaborative",
        "user-library-read",
        "user-read-private",
        "user-read-email"
    ]
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise SpotifyOAuthError(
                "Spotify OAuth not fully configured. "
                "Set SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI."
            )
    
    def get_authorization_url(self, user_id: int, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Spotify authorization URL for user consent.
        
        Args:
            user_id: ID of the user initiating OAuth flow
            state: Optional state parameter for CSRF protection
        
        Returns:
            Dict with 'url' and 'state'
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "show_dialog": False  # Set to True to force re-authentication
        }
        
        authorization_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        
        # Store state with user_id in cache for 10 minutes for CSRF validation
        cache.set(f"spotify_oauth_state_{state}", user_id, timeout=600)
        
        return {
            "url": authorization_url,
            "state": state
        }
    
    def validate_state(self, state: str) -> Optional[int]:
        """
        Validate OAuth state parameter and return associated user_id.
        
        Args:
            state: State parameter from callback
        
        Returns:
            User ID if valid, None otherwise
        """
        cache_key = f"spotify_oauth_state_{state}"
        user_id = cache.get(cache_key)
        
        if user_id:
            # Delete after validation (one-time use)
            cache.delete(cache_key)
            return user_id
        
        return None
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from callback
        
        Returns:
            Dict with token data
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully exchanged authorization code for tokens")
            
            return token_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise SpotifyOAuthError(f"Token exchange failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh an expired access token using refresh token.
        
        Args:
            refresh_token: The refresh token
        
        Returns:
            Dict with new token data
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully refreshed access token")
            
            return token_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            raise SpotifyOAuthError(f"Token refresh failed: {str(e)}")
    
    def save_token_for_user(self, user, token_data: Dict) -> SpotifyToken:
        """
        Save or update Spotify token for a user.
        
        Args:
            user: Django user instance
            token_data: Token data from Spotify
        
        Returns:
            SpotifyToken instance
        """
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")  # May not be present on refresh
        expires_in = token_data.get("expires_in", 3600)
        token_type = token_data.get("token_type", "Bearer")
        scope = token_data.get("scope", " ".join(self.SCOPES))
        
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Update or create token
        token, created = SpotifyToken.objects.update_or_create(
            user=user,
            defaults={
                "access_token": access_token,
                "token_type": token_type,
                "expires_at": expires_at,
                "scope": scope
            }
        )
        
        # Only update refresh_token if provided (not always returned on refresh)
        if refresh_token:
            token.refresh_token = refresh_token
            token.save(update_fields=["refresh_token"])
        
        action = "Created" if created else "Updated"
        logger.info(f"{action} Spotify token for user {user.username}")
        
        return token
    
    def get_valid_token_for_user(self, user) -> Optional[str]:
        """
        Get valid access token for user, refreshing if needed.
        
        Args:
            user: Django user instance
        
        Returns:
            Valid access token or None if not authenticated
        """
        try:
            token = SpotifyToken.objects.get(user=user)
        except SpotifyToken.DoesNotExist:
            logger.info(f"No Spotify token found for user {user.username}")
            return None
        
        # If token is expired or expiring soon, refresh it
        if token.is_expiring_soon(minutes=5):
            logger.info(f"Token expiring soon for user {user.username}, refreshing...")
            
            try:
                new_token_data = self.refresh_access_token(token.refresh_token)
                token = self.save_token_for_user(user, new_token_data)
            except SpotifyOAuthError as e:
                logger.error(f"Failed to refresh token for user {user.username}: {e}")
                # Token refresh failed, user needs to re-authenticate
                return None
        
        return token.access_token
    
    def revoke_token_for_user(self, user) -> bool:
        """
        Revoke (delete) Spotify token for user.
        
        Args:
            user: Django user instance
        
        Returns:
            True if token was deleted
        """
        try:
            token = SpotifyToken.objects.get(user=user)
            token.delete()
            logger.info(f"Revoked Spotify token for user {user.username}")
            return True
        except SpotifyToken.DoesNotExist:
            return False
    
    def make_authenticated_request(
        self, 
        user, 
        endpoint: str, 
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to Spotify API using user's token.
        
        Args:
            user: Django user instance
            endpoint: API endpoint (e.g., 'playlists/{id}')
            method: HTTP method
            params: Query parameters
            data: Request body data
        
        Returns:
            JSON response from Spotify API
        """
        access_token = self.get_valid_token_for_user(user)
        
        if not access_token:
            raise SpotifyOAuthError("User not authenticated with Spotify")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.API_BASE_URL}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            # If 401, token might be invalid even after refresh
            if e.response.status_code == 401:
                logger.warning(f"Authentication failed for user {user.username}")
                raise SpotifyOAuthError("Authentication failed. Please reconnect Spotify.")
            
            logger.error(f"Spotify API request failed: {e}")
            raise SpotifyOAuthError(f"Spotify API error: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request failed: {e}")
            raise SpotifyOAuthError(f"Spotify API error: {str(e)}")


# Global instance
spotify_oauth_service = SpotifyOAuthService()
