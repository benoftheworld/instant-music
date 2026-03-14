
"""Tests unitaires de YouTubeService."""

from unittest.mock import MagicMock, patch

from apps.playlists.youtube_service import YouTubeAPIError, YouTubeService
from tests.base import BaseUnitTest


class TestYouTubeServiceMakeRequest(BaseUnitTest):
    """Vérifie les méthodes de YouTubeService."""

    def get_target_class(self):
        return YouTubeService

    def setup_method(self):
        with patch("apps.playlists.youtube_service.settings") as mock_settings:
            mock_settings.YOUTUBE_API_KEY = "test_key"
            self.service = YouTubeService()

    @patch.object(YouTubeService, "_get_json")
    def test_make_request_adds_key(self, mock_get):
        mock_get.return_value = {"items": []}
        params = {"q": "rock"}
        self.service._make_request("search", params)
        assert params["key"] == "test_key"
        mock_get.assert_called_once()

    def test_make_request_no_api_key_raises(self):
        self.service.api_key = ""
        try:
            self.service._make_request("search", {})
            pytest.fail("Expected YouTubeAPIError")
        except YouTubeAPIError as e:
            assert "not configured" in str(e)

    def test_extract_http_error_json_body(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"message": "quota_exceeded"}}
        import requests

        err = requests.exceptions.HTTPError(response=mock_resp)
        result = self.service._extract_http_error_message(err)
        assert result == "quota_exceeded"

    def test_extract_http_error_no_json(self):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = Exception("no json")
        import requests

        err = requests.exceptions.HTTPError("test", response=mock_resp)
        result = self.service._extract_http_error_message(err)
        assert "test" in result
