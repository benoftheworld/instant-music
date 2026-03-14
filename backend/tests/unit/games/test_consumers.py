"""Tests unitaires des consumers WebSocket."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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
        consumer.send.assert_called_once_with(
            text_data=json.dumps({"type": "pong"})
        )

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
            consumer.unknown_method


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
        await consumer.broadcast_next_round({
            "round_data": {"round_number": 2},
            "updated_players": [{"name": "alice"}],
        })
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
        await consumer.broadcast_bonus_activated({
            "bonus": {"bonus_type": "freeze", "username": "alice"},
        })
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "bonus_activated"

    @pytest.mark.asyncio
    async def test_broadcast_bonus_with_extra_fields(self):
        from apps.games.consumers import GameConsumer

        consumer = GameConsumer()
        consumer.send = AsyncMock()
        await consumer.broadcast_bonus_activated({
            "bonus": {"bonus_type": "slow"},
            "new_duration": 15,
            "updated_players": [{"name": "bob"}],
        })
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
        assert validate_ws_message({"type": "activate_bonus", "bonus_type": "freeze"}) is None
