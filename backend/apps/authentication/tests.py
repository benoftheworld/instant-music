"""
Tests for authentication app.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTest(TestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
    
    def test_user_registration(self):
        """Test user can register."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
    
    def test_user_login(self):
        """Test user can login."""
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Login
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
