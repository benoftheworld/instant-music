"""Tests unitaires de la fonction validate_ws_message."""

from apps.games.consumers import validate_ws_message
from tests.base import BaseUnitTest


class TestValidateWsMessage(BaseUnitTest):
    """Vérifie la validation des messages WebSocket entrants."""

    def get_target_class(self):
        return validate_ws_message

    def test_missing_type_returns_error(self):
        result = validate_ws_message({})
        assert result is not None
        assert "type" in result

    def test_non_string_type_returns_error(self):
        result = validate_ws_message({"type": 123})
        assert result is not None
        assert "type" in result

    def test_unknown_type_returns_error(self):
        result = validate_ws_message({"type": "unknown_action"})
        assert result is not None
        assert "inconnu" in result

    def test_valid_ping(self):
        result = validate_ws_message({"type": "ping"})
        assert result is None

    def test_valid_player_join(self):
        result = validate_ws_message({"type": "player_join"})
        assert result is None

    def test_valid_activate_bonus_with_required_field(self):
        result = validate_ws_message({"type": "activate_bonus", "bonus_type": "fog"})
        assert result is None

    def test_activate_bonus_missing_required_field(self):
        result = validate_ws_message({"type": "activate_bonus"})
        assert result is not None
        assert "bonus_type" in result

    def test_valid_start_game(self):
        result = validate_ws_message({"type": "start_game"})
        assert result is None

    def test_valid_player_answer(self):
        result = validate_ws_message({"type": "player_answer"})
        assert result is None

    def test_valid_finish_game(self):
        result = validate_ws_message({"type": "finish_game"})
        assert result is None
