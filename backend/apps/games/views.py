"""
Views for games.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import random
import string

from .models import Game, GamePlayer, GameRound, GameAnswer
from .serializers import (
    GameSerializer,
    CreateGameSerializer,
    GamePlayerSerializer,
)


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Game.objects.filter(room_code=code).exists():
            return code


class GameViewSet(viewsets.ModelViewSet):
    """ViewSet for Game model."""
    
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'room_code'
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return CreateGameSerializer
        return GameSerializer
    
    def create(self, request):
        """Create a new game."""
        serializer = CreateGameSerializer(data=request.data)
        
        if serializer.is_valid():
            game = serializer.save(
                host=request.user,
                room_code=generate_room_code()
            )
            
            # Add host as a player
            GamePlayer.objects.create(
                game=game,
                user=request.user
            )
            
            return Response(
                GameSerializer(game).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def join(self, request, room_code=None):
        """Join a game."""
        game = self.get_object()
        
        # Check if game is joinable
        if game.status != 'waiting':
            return Response(
                {'error': 'La partie a déjà commencé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if game is full
        if game.players.count() >= game.max_players:
            return Response(
                {'error': 'La partie est pleine.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is already in the game
        if GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {'error': 'Vous êtes déjà dans cette partie.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add player to game
        player = GamePlayer.objects.create(
            game=game,
            user=request.user
        )
        
        return Response(
            GamePlayerSerializer(player).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, room_code=None):
        """Start a game."""
        game = self.get_object()
        
        # Check if user is the host
        if game.host != request.user:
            return Response(
                {'error': 'Seul l\'hôte peut démarrer la partie.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if there are enough players
        if game.players.count() < 2:
            return Response(
                {'error': 'Au moins 2 joueurs sont nécessaires.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update game status
        from django.utils import timezone
        game.status = 'in_progress'
        game.started_at = timezone.now()
        game.save()
        
        return Response(
            GameSerializer(game).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available games to join."""
        games = Game.objects.filter(
            status='waiting',
            is_online=True
        )
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)
