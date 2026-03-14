"""Protocole commun pour les services musicaux (Deezer, YouTube, etc.)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class MusicServiceProtocol(Protocol):
    """Contrat partagé entre les différentes sources musicales.

    Les deux implémentations (DeezerService, YouTubeService) respectent
    déjà cette interface — le Protocol formalise le contrat sans
    héritage.
    """

    def search_playlists(self, query: str, limit: int = 20) -> list[dict]:
        """Chercher des playlists par mot-clé."""
        ...

    def get_playlist(self, playlist_id: str) -> dict | None:
        """Récupérer les métadonnées d'une playlist."""
        ...

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> list[dict]:
        """Récupérer les pistes d'une playlist."""
        ...

    def search_music_videos(self, query: str, limit: int = 50) -> list[dict]:
        """Chercher des clips musicaux par mot-clé."""
        ...
