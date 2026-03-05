"""Vues de la boutique.
"""

import logging

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from apps.achievements.models import Achievement

from .models import GameBonus, ShopItem
from .serializers import (
    ActivateBonusSerializer,
    GameBonusSerializer,
    PurchaseSerializer,
    ShopItemSerializer,
    UserInventorySerializer,
)
from .services import (
    BonusAlreadyActiveError,
    InsufficientCoinsError,
    ItemNotAvailableError,
    bonus_service,
    shop_service,
)

logger = logging.getLogger("apps.shop.views")


class ShopViewSet(ReadOnlyModelViewSet):
    """Boutique virtuelle — liste et détail des articles disponibles.

    GET  /api/shop/items/          — catalogue complet
    GET  /api/shop/items/{id}/     — détail d'un article
    GET  /api/shop/items/summary/  — total pièces disponibles + solde utilisateur
    POST /api/shop/items/purchase/ — acheter un article
    """

    queryset = ShopItem.objects.filter(is_available=True).order_by("sort_order", "name")
    serializer_class = ShopItemSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Retourne un résumé de la boutique :
        - total_coins_available : total de pièces déblocables (tous achievements)
        - user_balance          : solde actuel de l'utilisateur
        - items_count           : nombre d'articles disponibles
        """
        total_available = (
            Achievement.objects.aggregate(total=Sum("points"))["total"] or 0
        )
        return Response(
            {
                "total_coins_available": total_available,
                "user_balance": request.user.coins_balance,
                "items_count": self.get_queryset().count(),
            }
        )

    @action(detail=False, methods=["post"])
    def purchase(self, request):
        """Acheter un article de la boutique."""
        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_id = serializer.validated_data["item_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            inventory = shop_service.purchase(
                request.user, item_id=item_id, quantity=quantity
            )
        except ItemNotAvailableError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientCoinsError as e:
            return Response({"detail": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)

        return Response(
            UserInventorySerializer(inventory).data,
            status=status.HTTP_201_CREATED,
        )


class InventoryViewSet(GenericViewSet):
    """Inventaire de l'utilisateur connecté.

    GET  /api/shop/inventory/            — liste des articles possédés
    POST /api/shop/inventory/activate/   — activer un bonus en partie
    GET  /api/shop/inventory/game/{code}/— bonus actifs pour une partie
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserInventorySerializer

    def list(self, request):
        """Retourner l'inventaire de l'utilisateur."""
        inventory = shop_service.get_user_inventory(request.user)
        serializer = UserInventorySerializer(inventory, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def activate(self, request):
        """Activer un bonus pour la partie en cours."""
        serializer = ActivateBonusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bonus_type = serializer.validated_data["bonus_type"]
        room_code = serializer.validated_data["room_code"]

        from apps.games.models import Game

        try:
            game = Game.objects.get(room_code=room_code)
        except Game.DoesNotExist:
            return Response(
                {"detail": "Partie introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Déterminer le round courant
        current_round = game.rounds.filter(
            started_at__isnull=False, ended_at__isnull=True
        ).first()
        round_number = current_round.round_number if current_round else None

        try:
            game_bonus = bonus_service.activate_bonus(
                request.user, game, bonus_type, round_number=round_number
            )
        except (ItemNotAvailableError, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BonusAlreadyActiveError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        # ── Effets immédiats selon le type de bonus ──────────────────────────
        extra_response: dict = {}

        from apps.games.models import GamePlayer

        if bonus_type == "fifty_fifty" and current_round:
            try:
                player = GamePlayer.objects.get(game=game, user=request.user)
                excluded = bonus_service.get_fifty_fifty_exclusions(
                    player=player,
                    round_number=round_number,  # type: ignore[arg-type]
                    options=current_round.options,
                    correct_answer=current_round.correct_answer,
                )
                extra_response["excluded_options"] = excluded
            except GamePlayer.DoesNotExist:
                pass

        elif bonus_type == "steal" and current_round:
            try:
                player = GamePlayer.objects.get(game=game, user=request.user)
                stolen = bonus_service.apply_steal_bonus(
                    player=player,
                    game=game,
                    round_number=round_number,  # type: ignore[arg-type]
                )
                extra_response["stolen_points"] = stolen
                # Diffuser les scores mis à jour
                updated_players = [
                    {
                        "id": str(p.id),
                        "username": p.user.username,
                        "score": p.score,
                    }
                    for p in game.players.select_related("user")
                ]
                extra_response["updated_players"] = updated_players
            except GamePlayer.DoesNotExist:
                pass

        elif bonus_type == "time_bonus" and current_round:
            new_duration = bonus_service.apply_time_bonus(
                player=request.user, round_obj=current_round
            )
            if new_duration:
                extra_response["new_duration"] = new_duration

        # Diffuser la notification via WebSocket
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer:
            ws_event: dict = {
                "type": "broadcast_bonus_activated",
                "bonus": {
                    "bonus_type": bonus_type,
                    "username": request.user.username,
                    "round_number": round_number,
                },
            }
            # Envoyer new_duration à tous pour synchroniser le timer
            if "new_duration" in extra_response:
                ws_event["new_duration"] = extra_response["new_duration"]
            # Envoyer les scores mis à jour à tous (vol de points)
            if "updated_players" in extra_response:
                ws_event["updated_players"] = extra_response["updated_players"]
            async_to_sync(channel_layer.group_send)(
                f"game_{room_code}",
                ws_event,
            )

        response_data = GameBonusSerializer(game_bonus).data
        response_data.update(extra_response)
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="game/(?P<room_code>[^/.]+)")
    def game_bonuses(self, request, room_code=None):
        """Lister les bonus actifs du joueur pour une partie donnée."""
        from apps.games.models import Game, GamePlayer

        try:
            game = Game.objects.get(room_code=room_code)
            player = GamePlayer.objects.get(game=game, user=request.user)
        except (Game.DoesNotExist, GamePlayer.DoesNotExist):
            return Response(
                {"detail": "Partie ou joueur introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        bonuses = GameBonus.objects.filter(player=player, is_used=False)
        return Response(GameBonusSerializer(bonuses, many=True).data)
