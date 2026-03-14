"""Tests unitaires de generate_room_code et _maintenance_response_if_needed."""

from unittest.mock import patch

from tests.base import BaseUnitTest


class TestGenerateRoomCode(BaseUnitTest):
    """Vérifie la génération de codes de salle."""

    def get_target_class(self):
        from apps.games.views.utils import generate_room_code

        return type(generate_room_code)

    @patch("apps.games.views.utils.Game")
    def test_returns_six_char_string(self, mock_game):
        from apps.games.views.utils import generate_room_code

        mock_game.objects.filter.return_value.exists.return_value = False
        code = generate_room_code()
        assert len(code) == 6
        assert code.isalnum()

    @patch("apps.games.views.utils.Game")
    def test_retries_on_collision(self, mock_game):
        from apps.games.views.utils import generate_room_code

        mock_game.objects.filter.return_value.exists.side_effect = [True, True, False]
        code = generate_room_code()
        assert len(code) == 6
        assert mock_game.objects.filter.return_value.exists.call_count == 3
