
"""Tests unitaires de BaseAPIService."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.playlists.base_api_service import BaseAPIService
from tests.base import BaseUnitTest


class TestBaseAPIServiceGetJson(BaseUnitTest):
    """Vérifie le comportement HTTP de BaseAPIService._get_json."""

    def get_target_class(self):
        return BaseAPIService

    def setup_method(self):
        self.service = BaseAPIService()
        self.service._error_class = RuntimeError

    @patch("apps.playlists.base_api_service.requests.get")
    def test_success_returns_json(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": "ok"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.service._get_json("http://example.com/api")
        assert result == {"data": "ok"}

    @patch("apps.playlists.base_api_service.requests.get")
    def test_http_error_raises(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_resp

        try:
            self.service._get_json("http://example.com/api")
            pytest.fail("Expected RuntimeError")
        except RuntimeError:
            pass

    @patch("apps.playlists.base_api_service.requests.get")
    def test_connection_error_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("refused")

        try:
            self.service._get_json("http://example.com/api")
            pytest.fail("Expected RuntimeError")
        except RuntimeError as e:
            assert "Request failed" in str(e)

    def test_extract_http_error_message_default(self):
        err = requests.exceptions.HTTPError("test error")
        result = self.service._extract_http_error_message(err)
        assert result == str(err)
