"""Abstract base class for external HTTP API services.

Factorise le boilerplate try/except + requests.get partagé par
DeezerService et YouTubeService.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class BaseAPIService:
    """Helper HTTP GET avec gestion d'erreurs unifiée pour les services API externes.

    Les sous-classes doivent définir :
      - BASE_URL (str)          — URL de base de l'API externe.
      - _error_class (type)     — exception à lever en cas d'échec.

    Les sous-classes peuvent surcharger :
      - _extract_http_error_message — pour extraire les détails d'erreur
        depuis le corps de la réponse HTTP (ex. YouTube renvoie un JSON
        ``{"error": {"message": "…"}}``).
    """

    BASE_URL: str = ""
    TIMEOUT: int = 10
    _error_class: type[Exception] = RuntimeError

    # ── Helper protégé ────────────────────────────────────────────────

    def _get_json(self, url: str, params: dict | None = None) -> dict:
        """Effectue un GET et retourne le corps JSON.

        Args:
            url: URL complète de la requête.
            params: Paramètres de requête optionnels.

        Returns:
            Réponse JSON désérialisée en dict.

        Raises:
            self._error_class: En cas d'erreur HTTP ou réseau.

        """
        try:
            response = requests.get(url, params=params or {}, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.HTTPError as e:
            msg = self._extract_http_error_message(e)
            logger.error("%s HTTP error on %s: %s", self.__class__.__name__, url, msg)
            raise self._error_class(msg) from e
        except requests.exceptions.RequestException as e:
            logger.error("%s request failed: %s", self.__class__.__name__, e)
            raise self._error_class(f"Request failed: {e}") from e

    def _extract_http_error_message(self, e: requests.exceptions.HTTPError) -> str:
        """Extrait un message lisible depuis une erreur HTTP.

        À surcharger dans les sous-classes dont l'API retourne des détails
        d'erreur structurés dans le corps de la réponse.
        """
        return str(e)
