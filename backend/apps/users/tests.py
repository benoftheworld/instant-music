"""
Tests for users app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user is created correctly."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        self.assertEqual(self.user.win_rate, 0.0)
        
        self.user.total_games_played = 10
        self.user.total_wins = 5
        self.user.save()
        
        self.assertEqual(self.user.win_rate, 50.0)
