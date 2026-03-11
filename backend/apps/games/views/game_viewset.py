"""ViewSet for Game model."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.throttles import GameCreateThrottle, GameJoinThrottle

from ..models import Game
from ..serializers import CreateGameSerializer, GameSerializer
from .game_discovery_mixin import GameDiscoveryMixin
from .game_invitation_mixin import GameInvitationMixin
from .game_lobby_mixin import GameLobbyMixin
from .game_results_mixin import GameResultsMixin
from .game_round_mixin import GameRoundMixin


class GameViewSet(
    GameLobbyMixin,
    GameRoundMixin,
    GameResultsMixin,
    GameDiscoveryMixin,
    GameInvitationMixin,
    viewsets.ModelViewSet,
):
    """ViewSet for Game model.

    Les actions sont réparties dans des mixins par domaine métier :
    - GameLobbyMixin      : create, join, leave, start, partial_update
    - GameRoundMixin      : current-round, answer, end-round, next-round
    - GameResultsMixin    : results, results/pdf
    - GameDiscoveryMixin  : public, history, leaderboard
    - GameInvitationMixin : invite, my-invitations, accept, decline
    """

    queryset = Game.objects.select_related("host")
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "room_code"

    def get_throttles(self):
        if self.action == "create":
            return [GameCreateThrottle()]
        if self.action == "join":
            return [GameJoinThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateGameSerializer
        return GameSerializer

