"""
Hybrid Spotify service that uses OAuth if available, otherwise falls back to Client Credentials.
"""
import logging
import re
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
        Automatically refreshes expiring tokens.
        
        Returns:
            tuple: (service, use_oauth: bool)
        """
        if user and user.is_authenticated:
            try:
                token = SpotifyToken.objects.get(user=user)
                # Auto-refresh if expiring soon
                if token.is_expiring_soon(minutes=5):
                    logger.info(f"Token expiring soon for {user.username}, refreshing...")
                    try:
                        new_token_data = self.oauth_service.refresh_access_token(token.refresh_token)
                        self.oauth_service.save_token_for_user(user, new_token_data)
                        logger.info(f"Using OAuth for user {user.username} (refreshed)")
                        return self.oauth_service, True
                    except Exception as e:
                        logger.warning(f"Token refresh failed for {user.username}: {e}")
                        # Fall through to client credentials
                elif not token.is_expired():
                    logger.info(f"Using OAuth for user {user.username}")
                    return self.oauth_service, True
            except SpotifyToken.DoesNotExist:
                pass
        
        logger.info("Using Client Credentials (fallback)")
        return self.client_service, False
    
    def search_playlists(self, query: str, limit: int = 20, user=None, public_only: bool = False) -> List[Dict]:
        """
        Search for playlists.
        
        Args:
            query: Search query
            limit: Max results
            user: Django user (optional, for OAuth)
            public_only: If True, filter to only show public playlists
        
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
                    }
                )
                
                playlists = response.get("playlists", {}).get("items", [])
                
                # Format playlists
                formatted = []
                for playlist in playlists:
                    if not playlist or not isinstance(playlist, dict):
                        continue
                    
                    # Filter for public playlists only if requested
                    if public_only and not playlist.get("public", False):
                        continue
                    
                    try:
                        formatted.append({
                            "spotify_id": playlist["id"],
                            "name": playlist["name"],
                            "description": playlist.get("description", ""),
                            "image_url": playlist["images"][0]["url"] if playlist.get("images") else "",
                            "total_tracks": playlist.get("tracks", {}).get("total", 0),
                            "owner": playlist.get("owner", {}).get("display_name", "Unknown"),
                            "external_url": playlist.get("external_urls", {}).get("spotify", ""),
                            "public": playlist.get("public", False)
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
        
        Strategy:
        1. Try /playlists/{id}/tracks endpoint (OAuth then CC)
        2. If 403 (Dev mode restriction), fall back to searching tracks
           based on the playlist name/description as search keywords.
        
        Args:
            playlist_id: Spotify playlist ID
            limit: Max tracks
            user: Django user (optional, for OAuth)
        
        Returns:
            List of tracks
        """
        # Strategy 1: Try direct playlist tracks endpoint
        tracks = self._try_get_playlist_tracks_direct(playlist_id, limit, user)
        if tracks:
            return tracks
        
        # Strategy 2: Fall back to searching tracks by playlist theme
        logger.info(f"Direct track access failed for {playlist_id}, using search-based fallback")
        return self._get_tracks_via_search(playlist_id, limit, user)
    
    def _try_get_playlist_tracks_direct(self, playlist_id: str, limit: int, user=None) -> List[Dict]:
        """Try to get tracks directly from the playlist tracks endpoint."""
        service, use_oauth = self._get_service_for_user(user)
        
        if use_oauth:
            try:
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
                        track = self._extract_track_from_item(item)
                        if track:
                            all_tracks.append(track)
                    
                    offset += len(items)
                    if len(items) < 50:
                        break
                
                if all_tracks:
                    logger.info(f"OAuth: got {len(all_tracks)} tracks from playlist {playlist_id}")
                    return all_tracks[:limit]
            
            except (SpotifyOAuthError, Exception) as e:
                logger.warning(f"OAuth tracks failed for {playlist_id}: {e}")
        
        # Try Client Credentials
        try:
            result = self.client_service.get_playlist_tracks(playlist_id, limit)
            if result:
                logger.info(f"Client Credentials: got {len(result)} tracks from playlist {playlist_id}")
                return result
        except Exception as e:
            logger.warning(f"Client Credentials tracks also failed for {playlist_id}: {e}")
        
        return []
    
    def _get_tracks_via_search(self, playlist_id: str, limit: int, user=None) -> List[Dict]:
        """
        Get tracks by searching Spotify based on the playlist's name/description.
        
        This is a fallback when direct playlist track access is blocked (403).
        Works by extracting keywords from the playlist name and searching for tracks.
        Each query tries OAuth first, then falls back to Client Credentials.
        """
        # Get the service to use (for search fallback)
        service, use_oauth = self._get_service_for_user(user)
        
        # Get playlist info using the method with proper fallback
        playlist_name = ""
        playlist_desc = ""
        
        try:
            playlist = self.get_playlist(playlist_id, user)
            if playlist and isinstance(playlist, dict):
                playlist_name = playlist.get("name", "")
                playlist_desc = playlist.get("description", "")
        except Exception as e:
            logger.warning("Could not get playlist info for %s: %s", playlist_id, e)
        
        if not playlist_name:
            playlist_name = "popular hits"
        
        # Extract meaningful search terms from playlist name
        search_queries = self._extract_search_queries(playlist_name, playlist_desc)
        logger.info("Search fallback for playlist '%s': queries=%s", playlist_name, search_queries)
        
        all_tracks = []
        seen_ids = set()
        
        for query in search_queries:
            if len(all_tracks) >= limit:
                break
            
            remaining = limit - len(all_tracks)
            tracks_needed = min(remaining + 5, 50)  # Get a few extra for dedup
            
            response = self._search_tracks_with_fallback(
                query, tracks_needed, service if use_oauth else None, user
            )
            
            if not response:
                continue
            
            items = response.get("tracks", {}).get("items", [])
            
            for track in items:
                if not track or not isinstance(track, dict):
                    continue
                
                track_id = track.get("id")
                if not track_id or track_id in seen_ids:
                    continue
                
                seen_ids.add(track_id)
                
                try:
                    all_tracks.append({
                        "spotify_id": track_id,
                        "name": track["name"],
                        "artists": [a["name"] for a in track.get("artists", [])],
                        "album": track.get("album", {}).get("name", "Unknown"),
                        "album_image": track["album"]["images"][0]["url"] if track.get("album", {}).get("images") else "",
                        "duration_ms": track.get("duration_ms", 0),
                        "preview_url": track.get("preview_url"),
                        "external_url": track.get("external_urls", {}).get("spotify", "")
                    })
                except (KeyError, IndexError, TypeError):
                    continue
        
        logger.info(f"Search fallback found {len(all_tracks)} tracks for playlist {playlist_id}")
        return all_tracks[:limit]
    
    def _search_tracks_with_fallback(self, query: str, limit: int, oauth_service=None, user=None) -> Optional[Dict]:
        """
        Search for tracks, trying OAuth first then falling back to Client Credentials.
        
        Args:
            query: Search query string
            limit: Max results
            oauth_service: OAuth service instance (None to skip OAuth)
            user: Django user for OAuth
        
        Returns:
            Spotify API response dict, or None if all attempts fail
        """
        search_params = {
            "q": query,
            "type": "track",
            "limit": limit,
        }
        
        # Try OAuth first
        if oauth_service and user:
            try:
                response = oauth_service.make_authenticated_request(
                    user=user,
                    endpoint="search",
                    params=search_params
                )
                return response
            except Exception as e:
                logger.warning(f"OAuth search for '{query}' failed, trying Client Credentials: {e}")
        
        # Fall back to Client Credentials
        try:
            response = self.client_service._make_request("search", search_params)
            return response
        except Exception as e:
            logger.warning(f"Client Credentials search for '{query}' also failed: {e}")
        
        return None
    
    def _extract_search_queries(self, playlist_name: str, description: str = "") -> List[str]:
        """
        Extract meaningful search queries from a playlist name and description.
        
        Examples:
        - "Top Hits 2026🔥Best popular songs" -> ["top hits 2026", "popular songs 2026"]
        - "80s HITS | TOP 100 SONGS" -> ["80s hits", "top songs 80s"]
        - "Rock Classics" -> ["rock classics", "classic rock"]
        - "COUNTRY HITS 2026" -> ["country hits 2026", "country music 2026"]
        """
        # Clean up the name
        clean_name = re.sub(r'[🔥🎵🎶🎤💿🎸⚠️]+', ' ', playlist_name)
        clean_name = re.sub(r'[|•·\-–—]+', ' ', clean_name)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip().lower()
        
        # Remove generic filler words
        filler_words = {'best', 'top', 'the', 'of', 'new', 'latest', 'most', 'songs', 
                       'music', 'playlist', 'mix', 'hits', 'tracks', 'no', 'social',
                       'media', 'accounts', 'associated', 'with', 'this', 'profile',
                       'beware', 'scams', 'trending', 'today', 'modern', 'viral',
                       'hottest', 'contemporary'}
        
        words = clean_name.split()
        
        # Extract decade/year references
        decade_match = re.search(r'(\d{2,4})s?', clean_name)
        era = decade_match.group(0) if decade_match else ""
        
        # Extract genre keywords (non-filler words)
        genre_words = [w for w in words if w not in filler_words and not re.match(r'^\d+$', w) and len(w) > 2]
        
        queries = []
        
        # Primary query: cleaned playlist name (truncated)
        primary = ' '.join(words[:5])
        if primary:
            queries.append(primary)
        
        # Genre-focused query
        if genre_words:
            genre_query = ' '.join(genre_words[:3])
            if era and era not in genre_query:
                genre_query += f" {era}"
            if genre_query not in queries:
                queries.append(genre_query)
        
        # Add some variety queries based on common patterns
        if era:
            era_query = f"hits {era}"
            if era_query not in queries:
                queries.append(era_query)
        
        # If we have genre words, create additional variations
        if genre_words and len(genre_words) >= 1:
            # Avoid duplicate words (e.g., "popular popular")
            if genre_words[0] != "popular":
                variation = f"{genre_words[0]} popular"
                if variation not in queries:
                    queries.append(variation)
        
        # Fallback
        if not queries:
            queries = ["popular hits", "top songs", "hit songs"]
        
        # Remove any queries with duplicate consecutive words
        filtered_queries = []
        for query in queries:
            words_in_query = query.split()
            if len(words_in_query) != len(set(words_in_query)):
                # Has duplicate words, skip it
                continue
            filtered_queries.append(query)
        
        return filtered_queries[:4] if filtered_queries else ["top songs"]  # Max 4 queries with fallback
    
    def _extract_track_from_item(self, item: dict) -> Optional[Dict]:
        """Extract track data from a playlist item."""
        if not item or "track" not in item:
            return None
        
        track = item["track"]
        if not track or not isinstance(track, dict):
            return None
        
        try:
            return {
                "spotify_id": track["id"],
                "name": track["name"],
                "artists": [artist["name"] for artist in track.get("artists", [])],
                "album": track.get("album", {}).get("name", "Unknown"),
                "album_image": track["album"]["images"][0]["url"] if track.get("album", {}).get("images") else "",
                "duration_ms": track.get("duration_ms", 0),
                "preview_url": track.get("preview_url"),
                "external_url": track.get("external_urls", {}).get("spotify", "")
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"Skipping malformed track: {e}")
            return None
    
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
