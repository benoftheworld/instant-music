"""Tests unitaires du RedactSensitiveParamsFilter."""

import logging

from apps.core.logging_middleware import RedactSensitiveParamsFilter
from tests.base import BaseUnitTest


class TestRedactSensitiveParamsFilter(BaseUnitTest):
    """Vérifie le masquage des paramètres sensibles dans les logs."""

    def get_target_class(self):
        return RedactSensitiveParamsFilter

    def setup_method(self):
        self.filter = RedactSensitiveParamsFilter()

    def test_redacts_token_in_msg(self):
        record = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "/ws/game/ABC123/?token=eyJ0eXAiOiJKV1Q", None, None,
        )
        self.filter.filter(record)
        assert "[REDACTED]" in record.msg
        assert "eyJ0eXAi" not in record.msg

    def test_redacts_access_token_in_args(self):
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "%s", ("/ws/?access_token=secret123",), None,
        )
        self.filter.filter(record)
        assert "[REDACTED]" in record.args[0]
        assert "secret123" not in record.args[0]

    def test_non_string_args_unchanged(self):
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "%d", (42,), None,
        )
        self.filter.filter(record)
        assert record.args == (42,)

    def test_no_sensitive_params_unchanged(self):
        record = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "/api/games/", None, None,
        )
        self.filter.filter(record)
        assert record.msg == "/api/games/"

    def test_returns_true_always(self):
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", None, None)
        assert self.filter.filter(record) is True
