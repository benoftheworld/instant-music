"""
Admin configuration for User models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model without first/last name."""

    list_display = [
        'username',
        'email',
        'is_staff',
        'total_games_played',
        'total_wins',
        'created_at',
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'created_at']
    search_fields = ['username', 'email']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Informations supplémentaires'), {'fields': ('avatar', 'bio', 'google_id')}),
        (_('Statistiques'), {'fields': ('total_games_played', 'total_wins', 'total_points')}),
        (_('Dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
