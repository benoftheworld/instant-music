"""
Admin configuration for User models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'total_games_played',
        'total_wins',
        'created_at',
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('avatar', 'bio', 'google_id')
        }),
        ('Statistiques', {
            'fields': ('total_games_played', 'total_wins', 'total_points')
        }),
    )
