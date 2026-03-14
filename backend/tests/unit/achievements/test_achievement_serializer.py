"""Tests unitaires du AchievementSerializer."""

from unittest.mock import MagicMock

from apps.achievements.serializers import AchievementSerializer
from tests.base import BaseSerializerUnitTest


class TestAchievementSerializer(BaseSerializerUnitTest):
    """Vérifie les champs et méthodes du serializer de succès."""

    def get_serializer_class(self):
        return AchievementSerializer

    def test_fields(self):
        serializer = AchievementSerializer()
        expected = {
            "id", "name", "description", "icon", "points",
            "condition_type", "condition_value", "unlocked", "unlocked_at",
        }
        assert set(serializer.fields.keys()) == expected

    def test_unlocked_is_method_field(self):
        from rest_framework import serializers
        field = AchievementSerializer().fields["unlocked"]
        assert isinstance(field, serializers.SerializerMethodField)

    def test_unlocked_at_is_method_field(self):
        from rest_framework import serializers
        field = AchievementSerializer().fields["unlocked_at"]
        assert isinstance(field, serializers.SerializerMethodField)

    def test_get_unlocked_with_context(self):
        """Quand user_achievements est dans le contexte, l'utilise."""
        achievement = MagicMock()
        achievement.id = 1
        context = {"user_achievements": {1: MagicMock()}}
        serializer = AchievementSerializer(context=context)
        result = serializer.get_unlocked(achievement)
        assert result is True

    def test_get_unlocked_not_in_context(self):
        """Quand le succès n'est pas débloqué."""
        achievement = MagicMock()
        achievement.id = 42
        context = {"user_achievements": {}}
        serializer = AchievementSerializer(context=context)
        result = serializer.get_unlocked(achievement)
        assert result is False
