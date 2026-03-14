"""Tests du broadcast_service : helpers internes."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestSerializeToDict(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie la conversion serializer → dict."""

    def test_converts_serializer_to_dict(self):
        from apps.games.broadcast_service import _serialize_to_dict

        mock_serializer = MagicMock()
        mock_serializer.data = {"key": "value", "number": 42}
        result = _serialize_to_dict(mock_serializer)
        assert result == {"key": "value", "number": 42}


class TestUuidSafe(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie la conversion récursive des UUID en str."""

    def test_uuid_converted_to_str(self):
        import uuid

        from apps.games.broadcast_service import _uuid_safe

        uid = uuid.uuid4()
        assert _uuid_safe(uid) == str(uid)

    def test_nested_dict_with_uuids(self):
        import uuid

        from apps.games.broadcast_service import _uuid_safe

        uid = uuid.uuid4()
        data = {"id": uid, "nested": {"other_id": uid}}
        result = _uuid_safe(data)
        assert result == {"id": str(uid), "nested": {"other_id": str(uid)}}

    def test_list_with_uuids(self):
        import uuid

        from apps.games.broadcast_service import _uuid_safe

        uid = uuid.uuid4()
        result = _uuid_safe([uid, "text", 123])
        assert result == [str(uid), "text", 123]

    def test_tuple_preserved(self):
        import uuid

        from apps.games.broadcast_service import _uuid_safe

        uid = uuid.uuid4()
        result = _uuid_safe((uid, "text"))
        assert isinstance(result, tuple)
        assert result == (str(uid), "text")

    def test_plain_values_unchanged(self):
        from apps.games.broadcast_service import _uuid_safe

        assert _uuid_safe("text") == "text"
        assert _uuid_safe(42) == 42
        assert _uuid_safe(None) is None


class TestGroupName(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie le format du nom de groupe."""

    def test_group_name(self):
        from apps.games.broadcast_service import _group_name

        assert _group_name("ABC123") == "game_ABC123"


class TestGroupSend(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie que _group_send appelle le channel layer."""

    @patch("apps.games.broadcast_service.get_channel_layer")
    @patch("apps.games.broadcast_service.async_to_sync")
    def test_sends_message_to_group(self, mock_async_to_sync, mock_get_cl):
        from apps.games.broadcast_service import _group_send

        mock_send = MagicMock()
        mock_async_to_sync.return_value = mock_send
        _group_send("ROOM1", {"type": "test_event"})
        mock_send.assert_called_once_with("game_ROOM1", {"type": "test_event"})


class TestBuildPlayerScores(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie la construction des scores par joueur."""

    @patch("apps.games.broadcast_service.GameAnswer")
    def test_builds_scores(self, mock_answer_cls):
        from apps.games.broadcast_service import _build_player_scores

        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_player = MagicMock()
        mock_player.user = mock_user
        mock_player.consecutive_correct = 3

        mock_ans = MagicMock()
        mock_ans.player = mock_player
        mock_ans.points_earned = 100
        mock_ans.is_correct = True
        mock_ans.response_time = 2.5
        mock_ans.streak_bonus = 10

        mock_answer_cls.objects.filter.return_value.select_related.return_value = [
            mock_ans
        ]

        round_obj = MagicMock()
        result = _build_player_scores(round_obj)
        assert "alice" in result
        assert result["alice"]["points_earned"] == 100
        assert result["alice"]["is_correct"] is True


class TestBuildUpdatedPlayers(BaseServiceUnitTest):
    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    """Vérifie la construction de la liste des joueurs."""

    def test_builds_players_list(self):
        from apps.games.broadcast_service import _build_updated_players

        mock_user = MagicMock()
        mock_user.id = "uid1"
        mock_user.username = "alice"
        mock_user.avatar = None

        mock_player = MagicMock()
        mock_player.id = "pid1"
        mock_player.user = mock_user
        mock_player.score = 200
        mock_player.rank = 1
        mock_player.consecutive_correct = 2
        mock_player.is_connected = True

        mock_game = MagicMock()
        mock_game.competitive_players.return_value.select_related.return_value.order_by.return_value = [  # noqa: E501
            mock_player
        ]

        result = _build_updated_players(mock_game)
        assert len(result) == 1
        assert result[0]["username"] == "alice"
        assert result[0]["score"] == 200


class TestBroadcastPlayerJoin(BaseServiceUnitTest):
    """Vérifie broadcast_player_join."""

    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    @patch("apps.games.broadcast_service._group_send")
    def test_broadcast_player_join(self, mock_send):
        from apps.games.broadcast_service import broadcast_player_join

        broadcast_player_join("ROOM1", {"user": "alice"}, {"id": "123"})
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_player_join"
        assert msg["player"] == {"user": "alice"}

    @patch("apps.games.broadcast_service._group_send")
    def test_broadcast_player_leave(self, mock_send):
        from apps.games.broadcast_service import broadcast_player_leave

        broadcast_player_leave("ROOM1", {"user": "alice"}, {"id": "123"})
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_player_leave"


class TestBroadcastGameEvents(BaseServiceUnitTest):
    """Vérifie broadcast_game_start/update/finish."""

    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    @patch("apps.games.broadcast_service._group_send")
    @patch("apps.games.broadcast_service.GameSerializer")
    def test_broadcast_game_start(self, mock_ser, mock_send):
        from apps.games.broadcast_service import broadcast_game_start

        mock_ser.return_value = MagicMock(data={"id": "1"})
        broadcast_game_start("ROOM1", MagicMock())
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_game_start"

    @patch("apps.games.broadcast_service._group_send")
    def test_broadcast_game_update(self, mock_send):
        from apps.games.broadcast_service import broadcast_game_update

        broadcast_game_update("ROOM1", {"id": "1"})
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_game_update"

    @patch("apps.games.broadcast_service._group_send")
    @patch("apps.games.broadcast_service._build_updated_players")
    @patch("apps.games.broadcast_service.GameSerializer")
    def test_broadcast_game_finish(self, mock_ser, mock_players, mock_send):
        from apps.games.broadcast_service import broadcast_game_finish

        mock_ser.return_value = MagicMock(data={"id": "1"})
        mock_players.return_value = [{"username": "alice", "score": 100}]
        broadcast_game_finish("ROOM1", MagicMock())
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_game_finish"


class TestBroadcastRoundEvents(BaseServiceUnitTest):
    """Vérifie broadcast_round_start/end/next."""

    def get_service_module(self):
        import apps.games.broadcast_service

        return apps.games.broadcast_service

    @patch("apps.games.broadcast_service._group_send")
    @patch("apps.games.broadcast_service._build_round_bonuses")
    @patch("apps.games.broadcast_service._check_and_consume_fog")
    @patch("apps.games.broadcast_service.GameRoundSerializer")
    def test_broadcast_round_start(self, mock_ser, mock_fog, mock_bonuses, mock_send):
        from apps.games.broadcast_service import broadcast_round_start

        round_obj = MagicMock(round_number=1)
        game = MagicMock()
        mock_ser.return_value = MagicMock(data={"id": "1"})
        mock_fog.return_value = (False, None)
        mock_bonuses.return_value = {}
        broadcast_round_start("ROOM1", round_obj, game)
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_round_start"

    @patch("apps.games.broadcast_service._group_send")
    @patch("apps.games.broadcast_service._build_round_bonuses")
    @patch("apps.games.broadcast_service._build_updated_players")
    @patch("apps.games.broadcast_service._build_player_scores")
    @patch("apps.games.broadcast_service.GameAnswer")
    @patch("apps.games.broadcast_service.GameRoundSerializer")
    def test_broadcast_round_end(
        self, mock_ser, mock_ga, mock_scores, mock_players, mock_bonuses, mock_send
    ):
        from apps.games.broadcast_service import broadcast_round_end

        round_obj = MagicMock(round_number=1, correct_answer="Song")
        game = MagicMock()
        game.players.all.return_value = []
        mock_ga.objects.filter.return_value.values_list.return_value = set()
        mock_ser.return_value = MagicMock(data={"id": "1"})
        mock_scores.return_value = {}
        mock_players.return_value = []
        mock_bonuses.return_value = []
        broadcast_round_end("ROOM1", round_obj, game)
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_round_end"
        assert "results" in msg

    @patch("apps.games.broadcast_service._group_send")
    @patch("apps.games.broadcast_service._build_updated_players")
    @patch("apps.games.broadcast_service._check_and_consume_fog")
    @patch("apps.games.broadcast_service.GameRoundSerializer")
    def test_broadcast_next_round(self, mock_ser, mock_fog, mock_players, mock_send):
        from apps.games.broadcast_service import broadcast_next_round

        round_obj = MagicMock(round_number=2)
        game = MagicMock()
        mock_ser.return_value = MagicMock(data={"id": "2"})
        mock_fog.return_value = (False, None)
        mock_players.return_value = []
        broadcast_next_round("ROOM1", round_obj, game)
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][1]
        assert msg["type"] == "broadcast_next_round"
