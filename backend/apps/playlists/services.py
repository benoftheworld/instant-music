"""
Spotify API service for fetching playlists and tracks.
"""
import base64
import logging
from typing import Dict, List, Optional
from datetime import timedelta
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors."""
    pass


class SpotifyService:
    """Service to interact with Spotify Web API."""
    
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    CACHE_TOKEN_KEY = "spotify_access_token"
    CACHE_TIMEOUT = 3000  # 50 minutes (to be safe before 1h expiration)
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            raise SpotifyAPIError(
                "Spotify credentials not configured. "
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in environment."
            )
    
    def _get_access_token(self) -> str:
        """
        Get Spotify access token using client credentials flow.
        Token is cached for 1 hour.
        """
        # Check cache first
        cached_token = cache.get(self.CACHE_TOKEN_KEY)
        if cached_token:
            return cached_token
        
        # Request new token
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            
            # Cache token with safety margin (90% of actual expiration time)
            cache_timeout = int(expires_in * 0.9)
            cache.set(self.CACHE_TOKEN_KEY, access_token, timeout=cache_timeout)
            
            logger.info(f"New Spotify token cached for {cache_timeout}s")
            return access_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Spotify access token: {e}")
            raise SpotifyAPIError(f"Failed to authenticate with Spotify: {str(e)}")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Spotify API.
        
        Args:
            endpoint: API endpoint (e.g., 'search', 'playlists/{id}')
            params: Query parameters
        
        Returns:
            JSON response from Spotify API
        """
        access_token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        url = f"{self.API_BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            # If 401 Unauthorized, token is definitely expired/invalid
            if e.response.status_code == 401:
                logger.warning("Spotify token expired (401), refreshing...")
                cache.delete(self.CACHE_TOKEN_KEY)
                
                # Retry with new token (only once to avoid infinite loop)
                try:
                    access_token = self._get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except Exception as retry_error:
                    logger.error(f"Retry after token refresh failed: {retry_error}")
                    raise SpotifyAPIError(f"Spotify API error after retry: {str(retry_error)}")
            
            # For other errors (like 400, 403, 404), don't retry
            logger.error(f"Spotify API request failed: {e}")
            raise SpotifyAPIError(f"Spotify API error: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request failed: {e}")
            raise SpotifyAPIError(f"Spotify API error: {str(e)}")
    
    def search_playlists(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for playlists on Spotify.
        
        Args:
            query: Search query string
            limit: Maximum number of results (default: 20)
        
        Returns:
            List of playlist dictionaries
        """
        cache_key = f"spotify_search_playlists_{quote(query)}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {
            "q": query,
            "type": "playlist",
            "limit": min(limit, 10),  # Spotify API max limit for playlists is 10
            "market": "US"
        }
        
        try:
            data = self._make_request("search", params)
            playlists = data.get("playlists", {}).get("items", [])
            
            # Format playlist data
            formatted_playlists = []
            for playlist in playlists:
                # Skip null/invalid playlists
                if not playlist or not isinstance(playlist, dict):
                    continue
                
                # Skip playlists without required fields (search results use 'items' not 'tracks')
                if not all(key in playlist for key in ["id", "name", "items", "owner"]):
                    continue
                
                try:
                    formatted_playlists.append({
                        "spotify_id": playlist["id"],
                        "name": playlist["name"],
                        "description": playlist.get("description", ""),
                        "image_url": playlist["images"][0]["url"] if playlist.get("images") and len(playlist["images"]) > 0 else "",
                        "total_tracks": playlist["items"]["total"],  # Search results use 'items' field
                        "owner": playlist["owner"].get("display_name", "Unknown"),
                        "external_url": playlist.get("external_urls", {}).get("spotify", "")
                    })
                except (KeyError, IndexError, TypeError) as format_error:
                    logger.warning(f"Skipping malformed playlist: {format_error}")
                    continue
            
            # Limit to requested number after filtering
            formatted_playlists = formatted_playlists[:limit]
            
            # Only cache non-empty results (don't cache failures)
            if formatted_playlists:
                cache.set(cache_key, formatted_playlists, timeout=1800)
            
            return formatted_playlists
        
        except Exception as e:
            logger.error(f"Failed to search playlists: {e}")
            # Don't cache errors - return empty list without caching
            return []
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        Get detailed playlist information.
        
        Args:
            playlist_id: Spotify playlist ID
        
        Returns:
            Playlist dictionary or None if not found
        """
        cache_key = f"spotify_playlist_{quote(playlist_id)}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            playlist = self._make_request(f"playlists/{playlist_id}")
            
            if not playlist or not isinstance(playlist, dict):
                logger.warning(f"Invalid playlist data for {playlist_id}")
                return None
            
            formatted_playlist = {
                "spotify_id": playlist.get("id", playlist_id),
                "name": playlist.get("name", "Unknown"),
                "description": playlist.get("description", ""),
                "image_url": playlist["images"][0]["url"] if playlist.get("images") and len(playlist["images"]) > 0 else "",
                "total_tracks": playlist.get("tracks", {}).get("total", 0),
                "owner": playlist.get("owner", {}).get("display_name", "Unknown"),
                "external_url": playlist.get("external_urls", {}).get("spotify", "")
            }
            
            # Cache for 1 hour
            cache.set(cache_key, formatted_playlist, timeout=3600)
            
            return formatted_playlist
        
        except Exception as e:
            logger.error(f"Failed to get playlist {playlist_id}: {e}")
            return None
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """
        Get tracks from a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            limit: Maximum number of tracks (default: 50, max: 100)
        
        Returns:
            List of track dictionaries
        """
        cache_key = f"spotify_playlist_tracks_{quote(playlist_id)}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            params = {"limit": min(limit, 100)}
            data = self._make_request(f"playlists/{playlist_id}/tracks", params)
            
            tracks = []
            for item in data.get("items", []):
                if not item or not isinstance(item, dict):
                    continue
                    
                track = item.get("track")
                if not track or not isinstance(track, dict):
                    continue
                
                # Skip tracks without required fields
                if not track.get("id") or not track.get("name"):
                    continue
                
                try:
                    tracks.append({
                        "spotify_id": track["id"],
                        "name": track["name"],
                        "artists": [artist["name"] for artist in track.get("artists", []) if artist.get("name")],
                        "album": track.get("album", {}).get("name", "Unknown"),
                        "album_image": track["album"]["images"][0]["url"] if track.get("album", {}).get("images") and len(track["album"]["images"]) > 0 else "",
                        "duration_ms": track.get("duration_ms", 0),
                        "preview_url": track.get("preview_url"),  # 30-second preview
                        "external_url": track.get("external_urls", {}).get("spotify", "")
                    })
                except (KeyError, IndexError, TypeError) as format_error:
                    logger.warning(f"Skipping malformed track: {format_error}")
                    continue
            
            # Cache for 1 hour
            cache.set(cache_key, tracks, timeout=3600)
            
            return tracks
        
        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {e}")
            return []
    
    def get_track(self, track_id: str) -> Optional[Dict]:
        """
        Get detailed track information.
        
        Args:
            track_id: Spotify track ID
        
        Returns:
            Track dictionary or None if not found
        """
        cache_key = f"spotify_track_{track_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            track = self._make_request(f"tracks/{track_id}")
            
            formatted_track = {
                "spotify_id": track["id"],
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": track["album"]["name"],
                "album_image": track["album"]["images"][0]["url"] if track["album"].get("images") else "",
                "duration_ms": track["duration_ms"],
                "preview_url": track.get("preview_url"),
                "external_url": track["external_urls"]["spotify"]
            }
            
            # Cache for 1 hour
            cache.set(cache_key, formatted_track, timeout=3600)
            
            return formatted_track
        
        except Exception as e:
            logger.error(f"Failed to get track {track_id}: {e}")
            return None


# Singleton instance
spotify_service = SpotifyService()
