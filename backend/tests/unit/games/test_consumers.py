"""Tests unitaires des consumers WebSocket."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.base import BaseServiceUnitTest


class TestNotificationConsumerConnect(BaseServiceUnitTest):
    """Vérifie la connexion du NotificationConsumer."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_connect_authenticated(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.id = 42
        consumer.scope = {"user": mock_user}
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.accept = AsyncMock()

        await consumer.connect()

        assert consumer.group_name == "notifications_42"
        consumer.channel_layer.group_add.assert_called_once()
        consumer.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_unauthenticated(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        consumer.scope = {"user": None}
        consumer.close = AsyncMock()

        await consumer.connect()
        consumer.close.assert_called_once()


class TestNotificationConsumerDisconnect(BaseServiceUnitTest):
    """Vérifie la déconnexion du NotificationConsumer."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_disconnect_with_group(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        consumer.group_name = "notifications_42"
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"

        await consumer.disconnect(1000)
        consumer.channel_layer.group_discard.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_without_group(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        # No group_name attribute → should not raise
        await consumer.disconnect(1000)


class TestNotificationConsumerReceive(BaseServiceUnitTest):
    """Vérifie la réception des messages du NotificationConsumer."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_ping_pong(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        consumer.send = AsyncMock()

        await consumer.receive(text_data=json.dumps({"type": "ping"}))
        consumer.send.assert_called_once_with(text_data=json.dumps({"type": "pong"}))

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        consumer.send = AsyncMock()
        # Should not raise
        await consumer.receive(text_data="not json{{{")
        consumer.send.assert_not_called()


class TestNotificationConsumerGetattr(BaseServiceUnitTest):
    """Vérifie le dispatch dynamique __getattr__."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_known_notification_type(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        consumer.send = AsyncMock()

        handler = consumer.notify_game_invitation
        await handler({"invitation": {"id": "inv1", "game": "G1"}})
        consumer.send.assert_called_once()
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "game_invitation"
        assert sent["invitation"] == {"id": "inv1", "game": "G1"}

    def test_unknown_attr_raises(self):
        from apps.games.consumers import NotificationConsumer

        consumer = NotificationConsumer()
        with pytest.raises(AttributeError):
            _ = consumer.unknown_method


class TestGameConsumerReceive(BaseServiceUnitTest):
    """Vérifie la réception des messages du GameConsumer."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_oversized_message(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        big_msg = "x" * (16 * 1024 + 1)
        await consumer.receive(text_data=big_msg)
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"
        assert "volumineux" in sent["message"]

    @pytest.mark.asyncio
    async def test_invalid_json_message(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.send = AsyncMock()
        await consumer.receive(text_data="not valid json")
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"
        assert "JSON" in sent["message"]

    @pytest.mark.asyncio
    async def test_ping_returns_pong(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.send = AsyncMock()
        await consumer.receive(text_data=json.dumps({"type": "ping"}))
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "pong"

    @pytest.mark.asyncio
    async def test_unknown_message_type(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.send = AsyncMock()
        msg = json.dumps({"type": "nonexistent_type"})
        await consumer.receive(text_data=msg)
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"
        assert "inconnu" in sent["message"]


class TestGameConsumerBroadcastHandlers(BaseServiceUnitTest):
    """Vérifie les handlers de broadcast du GameConsumer."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_broadcast_player_join(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        event = {"player": {"user": "u1"}, "game_data": {"status": "waiting"}}
        await consumer.broadcast_player_join(event)
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "player_joined"
        assert sent["player"] == {"user": "u1"}

    @pytest.mark.asyncio
    async def test_broadcast_player_leave(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        event = {"player": {"user": "u1"}, "game_data": {"status": "waiting"}}
        await consumer.broadcast_player_leave(event)
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "player_leave"

    @pytest.mark.asyncio
    async def test_broadcast_game_update(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_game_update({"game_data": {"id": "g1"}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "game_updated"

    @pytest.mark.asyncio
    async def test_broadcast_player_answer(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_player_answer({"player": "alice", "answered": True})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "player_answered"

    @pytest.mark.asyncio
    async def test_broadcast_all_answered(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_all_answered({})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "all_players_answered"

    @pytest.mark.asyncio
    async def test_broadcast_round_start(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_round_start({"round_data": {"round_number": 1}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "round_started"

    @pytest.mark.asyncio
    async def test_broadcast_round_end(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_round_end({"results": {"scores": {}}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "round_ended"

    @pytest.mark.asyncio
    async def test_broadcast_next_round(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_next_round({"round_data": {"round_number": 2}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "next_round"

    @pytest.mark.asyncio
    async def test_broadcast_next_round_with_players(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_next_round(
            {
                "round_data": {"round_number": 2},
                "updated_players": [{"name": "alice"}],
            }
        )
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert "updated_players" in sent

    @pytest.mark.asyncio
    async def test_broadcast_game_finish(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_game_finish({"results": {"winner": "alice"}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "game_finished"

    @pytest.mark.asyncio
    async def test_broadcast_game_start(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_game_start({"game_data": {"status": "playing"}})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "game_started"

    @pytest.mark.asyncio
    async def test_broadcast_bonus_activated(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_bonus_activated(
            {
                "bonus": {"bonus_type": "freeze", "username": "alice"},
            }
        )
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "bonus_activated"

    @pytest.mark.asyncio
    async def test_broadcast_bonus_with_extra_fields(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_bonus_activated(
            {
                "bonus": {"bonus_type": "slow"},
                "new_duration": 15,
                "updated_players": [{"name": "bob"}],
            }
        )
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["new_duration"] == 15
        assert "updated_players" in sent


class TestGameConsumerActivateBonus(BaseServiceUnitTest):
    """Vérifie activate_bonus."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_no_bonus_type(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(username="alice")}
        consumer.send = AsyncMock()

        await consumer.activate_bonus({"type": "activate_bonus"})
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"
        assert "bonus_type" in sent["message"]


class TestGameConsumerRequireHost(BaseServiceUnitTest):
    """Vérifie _require_host."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_is_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer._is_host = AsyncMock(return_value=True)
        consumer.send = AsyncMock()

        result = await consumer._require_host("start_game")
        assert result is True
        consumer.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_not_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=2)}
        consumer.room_code = "ROOM1"
        consumer._is_host = AsyncMock(return_value=False)
        consumer.send = AsyncMock()

        result = await consumer._require_host("start_game")
        assert result is False
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"


class TestValidateWsMessage(BaseServiceUnitTest):
    """Vérifie validate_ws_message."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    def test_valid_ping(self):
        from apps.games.consumers import validate_ws_message

        assert validate_ws_message({"type": "ping"}) is None

    def test_missing_type(self):
        from apps.games.consumers import validate_ws_message

        result = validate_ws_message({})
        assert result is not None

    def test_unknown_type(self):
        from apps.games.consumers import validate_ws_message

        result = validate_ws_message({"type": "nonexistent"})
        assert result is not None
        assert "inconnu" in result

    def test_missing_required_fields(self):
        from apps.games.consumers import validate_ws_message

        result = validate_ws_message({"type": "activate_bonus"})
        assert result is not None
        assert "bonus_type" in result

    def test_valid_with_required(self):
        from apps.games.consumers import validate_ws_message

        assert (
            validate_ws_message({"type": "activate_bonus", "bonus_type": "freeze"})
            is None
        )

    def test_non_string_type(self):
        from apps.games.consumers import validate_ws_message

        result = validate_ws_message({"type": 123})
        assert result is not None
        assert "type" in result

    def test_all_schema_types_valid(self):
        """Couvre tous les types de messages connus sans champs requis."""
        from apps.games.consumers import WS_MESSAGE_SCHEMAS, validate_ws_message

        for msg_type, schema in WS_MESSAGE_SCHEMAS.items():
            data = {"type": msg_type}
            for field in schema.get("required", set()):
                data[field] = "test_value"
            assert validate_ws_message(data) is None, f"Failed for type: {msg_type}"


class TestGameConsumerConnect(BaseServiceUnitTest):
    """Vérifie GameConsumer.connect."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    @patch("apps.games.consumers.WS_CONNECTIONS_ACTIVE")
    @patch("apps.games.consumers.WS_CONNECTIONS_TOTAL")
    async def test_connect_success(self, mock_total, mock_active):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        user = MagicMock(id=42, username="alice", is_authenticated=True)
        consumer.scope = {
            "user": user,
            "url_route": {"kwargs": {"room_code": "ABCDEF"}},
        }
        consumer.channel_name = "ch1"
        consumer.channel_layer = AsyncMock()
        consumer.accept = AsyncMock()
        consumer.send = AsyncMock()
        consumer._set_player_connected = AsyncMock()
        consumer.get_game_data = AsyncMock(return_value={"players": []})

        await consumer.connect()

        assert consumer.room_code == "ABCDEF"
        assert consumer.room_group_name == "game_ABCDEF"
        consumer.channel_layer.group_add.assert_called_once()
        consumer.accept.assert_called_once()
        consumer._set_player_connected.assert_called_once_with(True)
        # Should send connection_established + broadcast player_join
        assert consumer.send.call_count >= 1
        consumer.channel_layer.group_send.assert_called_once()


class TestGameConsumerDisconnect(BaseServiceUnitTest):
    """Vérifie GameConsumer.disconnect."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    @patch("apps.games.consumers.WS_CONNECTIONS_ACTIVE")
    @patch("apps.games.consumers.WS_CONNECTIONS_TOTAL")
    async def test_disconnect_authenticated(self, mock_total, mock_active):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        user = MagicMock(id=42, username="alice", is_authenticated=True)
        consumer.scope = {"user": user}
        consumer.room_code = "ABCDEF"
        consumer.room_group_name = "game_ABCDEF"
        consumer.channel_name = "ch1"
        consumer.channel_layer = AsyncMock()
        consumer._set_player_connected = AsyncMock()
        consumer.get_game_data = AsyncMock(return_value={"players": []})

        await consumer.disconnect(1000)

        consumer.channel_layer.group_discard.assert_called_once()
        consumer._set_player_connected.assert_called_once_with(False)
        consumer.get_game_data.assert_called_once()
        consumer.channel_layer.group_send.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.games.consumers.WS_CONNECTIONS_ACTIVE")
    @patch("apps.games.consumers.WS_CONNECTIONS_TOTAL")
    async def test_disconnect_unauthenticated(self, mock_total, mock_active):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": None}
        consumer.room_code = "ABCDEF"
        consumer.room_group_name = "game_ABCDEF"
        consumer.channel_name = "ch1"
        consumer.channel_layer = AsyncMock()

        await consumer.disconnect(1000)

        consumer.channel_layer.group_discard.assert_called_once()
        # Should not attempt broadcast for unauthenticated
        consumer.channel_layer.group_send.assert_not_called()


class TestGameConsumerRateLimit(BaseServiceUnitTest):
    """Vérifie _check_rate_limit."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    @patch("apps.games.consumers._get_ws_redis")
    async def test_rate_limit_allowed(self, mock_redis_fn):
        from apps.games.consumers import GameConsumer

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)
        mock_redis_fn.return_value = mock_redis

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"

        result = await consumer._check_rate_limit("player_join")
        assert result is True

    @pytest.mark.asyncio
    @patch("apps.games.consumers._get_ws_redis")
    async def test_rate_limit_throttled(self, mock_redis_fn):
        from apps.games.consumers import GameConsumer

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=0)
        mock_redis_fn.return_value = mock_redis

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"

        result = await consumer._check_rate_limit("player_answer")
        assert result is False

    @pytest.mark.asyncio
    @patch("apps.games.consumers._get_ws_redis")
    async def test_rate_limit_redis_error_fails_closed(self, mock_redis_fn):
        from apps.games.consumers import GameConsumer

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=Exception("Redis down"))
        mock_redis_fn.return_value = mock_redis

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"

        result = await consumer._check_rate_limit("start_game")
        assert result is False

    @pytest.mark.asyncio
    @patch("apps.games.consumers._get_ws_redis")
    async def test_rate_limit_default_limits(self, mock_redis_fn):
        from apps.games.consumers import GameConsumer

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)
        mock_redis_fn.return_value = mock_redis

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"

        # Unknown type should use _default limits
        result = await consumer._check_rate_limit("some_unknown_type")
        assert result is True


class TestGameConsumerReceiveRouting(BaseServiceUnitTest):
    """Vérifie le routage depuis GameConsumer.receive."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    def _make_consumer(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.room_code = "ABCDEF"
        consumer.room_group_name = "game_ABCDEF"
        consumer.scope = {"user": MagicMock(id=1, is_authenticated=True)}
        consumer.channel_name = "ch1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        return consumer

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_route_player_join(self, mock_rl):
        consumer = self._make_consumer()
        consumer.player_join = AsyncMock()
        await consumer.receive(text_data=json.dumps({"type": "player_join"}))
        consumer.player_join.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_route_player_answer(self, mock_rl):
        consumer = self._make_consumer()
        consumer.player_answer = AsyncMock()
        await consumer.receive(text_data=json.dumps({"type": "player_answer"}))
        consumer.player_answer.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_route_start_game(self, mock_rl):
        consumer = self._make_consumer()
        consumer.start_game = AsyncMock()
        await consumer.receive(text_data=json.dumps({"type": "start_game"}))
        consumer.start_game.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_route_activate_bonus(self, mock_rl):
        consumer = self._make_consumer()
        consumer.activate_bonus = AsyncMock()
        await consumer.receive(
            text_data=json.dumps({"type": "activate_bonus", "bonus_type": "fog"})
        )
        consumer.activate_bonus.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=True,
    )
    async def test_handler_exception_sends_error(self, mock_rl):
        consumer = self._make_consumer()
        consumer.player_join = AsyncMock(side_effect=RuntimeError("boom"))
        await consumer.receive(text_data=json.dumps({"type": "player_join"}))
        # Last send should be the error
        calls = consumer.send.call_args_list
        last_sent = json.loads(calls[-1][1]["text_data"])
        assert last_sent["type"] == "error"
        assert "interne" in last_sent["message"]

    @pytest.mark.asyncio
    @patch(
        "apps.games.consumers.GameConsumer._check_rate_limit",
        new_callable=AsyncMock,
        return_value=False,
    )
    async def test_rate_limited_returns_error(self, mock_rl):
        consumer = self._make_consumer()
        await consumer.receive(text_data=json.dumps({"type": "player_join"}))
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert "patienter" in sent["message"]


class TestGameConsumerPlayerAnswer(BaseServiceUnitTest):
    """Vérifie player_answer handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_player_answer_broadcasts(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(username="alice")}
        consumer.room_group_name = "game_ROOM1"
        consumer.room_code = "ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer._check_all_party_players_answered = AsyncMock(return_value=False)

        await consumer.player_answer({"type": "player_answer", "answer": "test"})

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_player_answer"
        assert call[0][1]["player"] == "alice"

    @pytest.mark.asyncio
    async def test_player_answer_all_answered_party_mode(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(username="alice")}
        consumer.room_group_name = "game_ROOM1"
        consumer.room_code = "ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer._check_all_party_players_answered = AsyncMock(return_value=True)

        await consumer.player_answer({"type": "player_answer"})

        assert consumer.channel_layer.group_send.call_count == 2
        second_call = consumer.channel_layer.group_send.call_args_list[1]
        assert second_call[0][1]["type"] == "broadcast_all_answered"


class TestGameConsumerStartGame(BaseServiceUnitTest):
    """Vérifie start_game handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_start_game_as_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        consumer._require_host = AsyncMock(return_value=True)  # type: ignore[method-assign]
        consumer.get_game_data = AsyncMock(return_value={"status": "playing"})

        await consumer.start_game({"type": "start_game"})

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_game_start"

    @pytest.mark.asyncio
    async def test_start_game_not_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=2)}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        consumer._require_host = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await consumer.start_game({"type": "start_game"})

        consumer.channel_layer.group_send.assert_not_called()


class TestGameConsumerStartRound(BaseServiceUnitTest):
    """Vérifie start_round handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_start_round_as_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        consumer._require_host = AsyncMock(return_value=True)  # type: ignore[method-assign]
        consumer._enrich_round_data_with_fog = AsyncMock(  # type: ignore[method-assign]
            return_value={"round_number": 1}
        )

        await consumer.start_round(
            {"type": "start_round", "round_data": {"round_number": 1}}
        )

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_round_start"

    @pytest.mark.asyncio
    async def test_start_round_not_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._require_host = AsyncMock(return_value=False)  # type: ignore[method-assign]
        consumer.channel_layer = AsyncMock()

        await consumer.start_round({"type": "start_round"})

        consumer.channel_layer.group_send.assert_not_called()


class TestGameConsumerEndRound(BaseServiceUnitTest):
    """Vérifie end_round handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_end_round_as_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(id=1)}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer._require_host = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await consumer.end_round({"type": "end_round", "results": {"scores": {}}})

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_round_end"


class TestGameConsumerNextRound(BaseServiceUnitTest):
    """Vérifie next_round handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_next_round_as_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._require_host = AsyncMock(return_value=True)  # type: ignore[method-assign]
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer._enrich_round_data_with_fog = AsyncMock(  # type: ignore[method-assign]
            return_value={"round_number": 2}
        )

        await consumer.next_round(
            {"type": "next_round", "round_data": {"round_number": 2}}
        )

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_next_round"


class TestGameConsumerFinishGame(BaseServiceUnitTest):
    """Vérifie finish_game handler."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_finish_game_as_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._require_host = AsyncMock(return_value=True)  # type: ignore[method-assign]
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()

        await consumer.finish_game(
            {"type": "finish_game", "results": {"winner": "alice"}}
        )

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_game_finish"

    @pytest.mark.asyncio
    async def test_finish_game_not_host(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._require_host = AsyncMock(return_value=False)  # type: ignore[method-assign]
        consumer.channel_layer = AsyncMock()

        await consumer.finish_game({"type": "finish_game"})

        consumer.channel_layer.group_send.assert_not_called()


class TestGameConsumerActivateBonusHandler(BaseServiceUnitTest):
    """Vérifie activate_bonus handler complet."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_activate_bonus_success(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(username="alice")}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        consumer._do_activate_bonus = AsyncMock(return_value={"round_number": 3})

        await consumer.activate_bonus({"type": "activate_bonus", "bonus_type": "fog"})

        consumer.channel_layer.group_send.assert_called_once()
        call = consumer.channel_layer.group_send.call_args
        assert call[0][1]["type"] == "broadcast_bonus_activated"
        assert call[0][1]["bonus"]["bonus_type"] == "fog"
        assert call[0][1]["bonus"]["username"] == "alice"

    @pytest.mark.asyncio
    async def test_activate_bonus_error(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.scope = {"user": MagicMock(username="alice")}
        consumer.room_code = "ROOM1"
        consumer.room_group_name = "game_ROOM1"
        consumer.channel_layer = AsyncMock()
        consumer.send = AsyncMock()
        consumer._do_activate_bonus = AsyncMock(
            return_value={"error": "Bonus indisponible."}
        )

        await consumer.activate_bonus({"type": "activate_bonus", "bonus_type": "fog"})

        consumer.channel_layer.group_send.assert_not_called()
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "error"
        assert "indisponible" in sent["message"]


class TestGameConsumerEnrichRoundData(BaseServiceUnitTest):
    """Vérifie _enrich_round_data_with_fog."""

    def get_service_module(self):
        import apps.games.consumers

        return apps.games.consumers

    @pytest.mark.asyncio
    async def test_no_round_number(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._check_and_consume_fog = AsyncMock()

        result = await consumer._enrich_round_data_with_fog({})

        consumer._check_and_consume_fog.assert_not_called()
        assert result == {}

    @pytest.mark.asyncio
    async def test_fog_active(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._check_and_consume_fog = AsyncMock(return_value=(True, "alice"))

        result = await consumer._enrich_round_data_with_fog({"round_number": 3})

        assert result["fog_active"] is True
        assert result["fog_activator"] == "alice"

    @pytest.mark.asyncio
    async def test_fog_not_active(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._check_and_consume_fog = AsyncMock(return_value=(False, None))

        result = await consumer._enrich_round_data_with_fog({"round_number": 3})

        assert "fog_active" not in result

    @pytest.mark.asyncio
    async def test_none_round_data(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer._check_and_consume_fog = AsyncMock()

        result = await consumer._enrich_round_data_with_fog(None)  # type: ignore[arg-type]

        assert result is None
        consumer._check_and_consume_fog.assert_not_called()
