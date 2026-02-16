"""
Hybrid Spotify service that uses OAuth if available, otherwise falls back to Client Credentials.
"""
import logging
from typing import Dict, List, Optional

from .services import spotify_service, SpotifyAPIError
from .oauth import spotify_oauth_service, SpotifyOAuthError
from .models import SpotifyToken

logger = logging.getLogger(__name__)


class HybridSpotifyService:
    """
    Service that intelligently chooses between OAuth and Client Credentials.
    
    - If user has connected Spotify (OAuth token exists): Use OAuth
    - Otherwise: Use Client Credentials (limited access)
    """
    
    def __init__(self):
        self.client_service = spotify_service
        self.oauth_service = spotify_oauth_service
    
    def _get_service_for_user(self, user):
        """
        Determine which service to use for the given user.
        
        Returns:
            tuple: (service, use_oauth: bool)
        """
        if user and user.is_authenticated:
            try:
                token = SpotifyToken.objects.get(user=user)
                if not token.is_expired():
                    logger.info(f"Using OAuth for user {user.username}")
                    return self.oauth_service, True
            except SpotifyToken.DoesNotExist:
                pass
        
        logger.info("Using Client Credentials (fallback)")
        return self.client_service, False
    
    def search_playlists(self, query: str, limit: int = 20, user=None) -> List[Dict]:
        """
        Search for playlists.
        
        Args:
            query: Search query
            limit: Max results
            user: Django user (optional, for OAuth)
        
        Returns:
            List of playlists
        """
        service, use_oauth = self._get_service_for_user(user)
        
        if use_oauth:
            try:
                # Use OAuth to search
                response = service.make_authenticated_request(
                    user=user,
                    endpoint="search",
                    params={
                        "q": query,
                        "type": "playlist",
                        "limit": min(limit, 50),
                        "market": "US"
                    }
                )
                
                playlists = response.get("playlists", {}).get("items", [])
                
                # Format playlists
                formatted = []
                for playlist in playlists:
                    if not playlist or not isinstance(playlist, dict):
                        continue
                    
                    try:
                        formatted.append({
                            "spotify_id": playlist["id"],
                            "name": playlist["name"],
                            "description": playlist.get("description", ""),
                            "image_url": playlist["images"][0]["url"] if playlist.get("images") else "",
                            "total_tracks": playlist.get("tracks", {}).get("total", 0),
                            "owner": playlist.get("owner", {}).get("display_name", "Unknown"),
                            "external_url": playlist.get("external_urls", {}).get("spotify", "")
                        })
                    except (KeyError, IndexError, TypeError) as e:
                        logger.warning(f"Skipping malformed playlist: {e}")
                        continue
                
                return formatted[:limit]
            
            except (SpotifyOAuthError, Exception) as e:
                logger.warning(f"OAuth search failed, falling back to Client Credentials: {e}")
                # Fall back to client credentials
                return self.client_service.search_playlists(query, limit)
        else:
            # Use Client Credentials
            return self.client_service.search_playlists(query, limit)
    
    def get_playlist(self, playlist_id: str, user=None) -> Optional[Dict]:
        """
        Get playlist details.
        
        Args:
            playlist_id: Spotify playlist ID
            user: Django user (optional, for OAuth)
        
        Returns:
            Playlist dict or None
        """
        service, use_oauth = self._get_service_for_user(user)
        
        if use_oauth:
            try:
                # Use OAuth
                playlist = service.make_authenticated_request(
                    user=user,
                    endpoint=f"playlists/{playlist_id}"
                )
                
                return {
                    "spotify_id": playlist.get("id", playlist_id),
                    "name": playlist.get("name", "Unknown"),
                    "description": playlist.get("description", ""),
                    "image_url": playlist["images"][0]["url"] if playlist.get("images") else "",
                    "total_tracks": playlist.get("tracks", {}).get("total", 0),
                    "owner": playlist.get("owner", {}).get("display_name", "Unknown"),
                    "external_url": playlist.get("external_urls", {}).get("spotify", "")
                }
            
            except (SpotifyOAuthError, Exception) as e:
                logger.warning(f"OAuth get_playlist failed, falling back: {e}")
                return self.client_service.get_playlist(playlist_id)
        else:
            return self.client_service.get_playlist(playlist_id)
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 50, user=None) -> List[Dict]:
        """
        Get tracks from a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            limit: Max tracks
            user: Django user (optional, for OAuth)
        
        Returns:
            List of tracks
        """
        service, use_oauth = self._get_service_for_user(user)
        
        if use_oauth:
            try:
                # Use OAuth to get tracks
                all_tracks = []
                offset = 0
                
                while len(all_tracks) < limit:
                    response = service.make_authenticated_request(
                        user=user,
                        endpoint=f"playlists/{playlist_id}/tracks",
                        params={
                            "limit": min(50, limit - len(all_tracks)),
                            "offset": offset
                        }
                    )
                    
                    items = response.get("items", [])
                    if not items:
                        break
                    
                    for item in items:
                        if not item or "track" not in item:
                            continue
                        
                        track = item["track"]
                        if not track or not isinstance(track, dict):
                            continue
                        
                        try:
                            all_tracks.append({
                                "spotify_id": track["id"],
                                "name": track["name"],
                                "artists": [artist["name"] for artist in track.get("artists", [])],
                                "album": track.get("album", {}).get("name", "Unknown"),
                                "album_image": track["album"]["images"][0]["url"] if track.get("album", {}).get("images") else "",
                                "duration_ms": track.get("duration_ms", 0),
                                "preview_url": track.get("preview_url"),
                                "external_url": track.get("external_urls", {}).get("spotify", "")
                            })
                        except (KeyError, IndexError, TypeError) as e:
                            logger.warning(f"Skipping malformed track: {e}")
                            continue
                    
                    offset += len(items)
                    
                    if len(items) < 50:
                        break
                
                return all_tracks[:limit]
            
            except (SpotifyOAuthError, Exception) as e:
                logger.warning(f"OAuth get_tracks failed, falling back: {e}")
                return self.client_service.get_playlist_tracks(playlist_id, limit)
        else:
            return self.client_service.get_playlist_tracks(playlist_id, limit)
    
    def is_using_oauth(self, user) -> bool:
        """Check if OAuth is available for user."""
        if not user or not user.is_authenticated:
            return False
        
        try:
            token = SpotifyToken.objects.get(user=user)
            return not token.is_expired()
        except SpotifyToken.DoesNotExist:
            return False


# Global instance
hybrid_spotify_service = HybridSpotifyService()
