"""Serializers pour les modèles de succès et de succès débloqués."""

from rest_framework import serializers

from .models import Achievement, UserAchievement


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer des succès."""

    unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()

    class Meta:
        """Meta options for the AchievementSerializer."""

        model = Achievement
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "points",
            "condition_type",
            "condition_value",
            "unlocked",
            "unlocked_at",
        ]

    def _get_user_achievement(self, obj):
        """Retourne l'instance UserAchievement pour cet objet et l'utilisateur.

        Args:
            obj (Achievement): L'instance d'Achievement pour laquelle vérifier
                le déblocage.

        Returns:
            UserAchievement ou None: L'instance UserAchievement si l'utilisateur
                a débloqué ce succès, sinon None.

        """
        # Fast path: pre-fetched map supplied by the view
        ua_map = self.context.get("user_achievements")
        if ua_map is not None:
            return ua_map.get(obj.id)

        # Fallback (single-object serialization)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return UserAchievement.objects.filter(
                user=request.user, achievement=obj
            ).first()
        return None

    def get_unlocked(self, obj):
        """Return True if the current user has unlocked this achievement."""
        return self._get_user_achievement(obj) is not None

    def get_unlocked_at(self, obj):
        """Return the timestamp when the user unlocked the achievement."""
        ua = self._get_user_achievement(obj)
        if ua:
            return ua.unlocked_at.isoformat()
        return None


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer pour UserAchievement, avec détails de l'achievement."""

    achievement = AchievementSerializer(read_only=True)

    class Meta:
        """Meta options for the UserAchievementSerializer."""

        model = UserAchievement
        fields = ["id", "achievement", "unlocked_at"]
