"""
Tests for games app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Game, GamePlayer

User = get_user_model()


class GameModelTest(TestCase):
    """Test Game model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.game = Game.objects.create(
            host=self.user, room_code="ABC123", mode="classique"
        )

    def test_game_creation(self):
        """Test game is created correctly."""
        self.assertEqual(self.game.room_code, "ABC123")
        self.assertEqual(self.game.host, self.user)
        self.assertEqual(self.game.status, "waiting")

    def test_add_player_to_game(self):
        """Test adding a player to a game."""
        player = GamePlayer.objects.create(game=self.game, user=self.user)
        self.assertEqual(self.game.players.count(), 1)
        self.assertEqual(player.score, 0)
