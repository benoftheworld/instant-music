"""Factories pour les tests — Factory-Boy.

Chaque factory crée une instance de modèle avec des valeurs
réalistes par défaut, utilisable dans les tests unitaires (mock)
et d'intégration (avec DB).
"""

import uuid

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()


# ╔══════════════════════════════════════════════════════════════════╗
# ║                           USERS                                  ║
# ╚══════════════════════════════════════════════════════════════════╝


class UserFactory(DjangoModelFactory):
    """Factory pour le modèle User."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "Testpass123!")
    is_active = True
    is_staff = False

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Sauvegarder après set_password pour persister le hash."""
        super()._after_postgeneration(instance, create, results)
        if create:
            instance.save()


class FriendshipFactory(DjangoModelFactory):
    """Factory pour le modèle Friendship."""

    class Meta:
        model = "users.Friendship"

    from_user = factory.SubFactory(UserFactory)
    to_user = factory.SubFactory(UserFactory)
    status = "pending"


class TeamFactory(DjangoModelFactory):
    """Factory pour le modèle Team."""

    class Meta:
        model = "users.Team"

    name = factory.Sequence(lambda n: f"Team {n}")
    description = "Description de test"
    owner = factory.SubFactory(UserFactory)


class TeamMemberFactory(DjangoModelFactory):
    """Factory pour le modèle TeamMember."""

    class Meta:
        model = "users.TeamMember"

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    role = "member"


class TeamJoinRequestFactory(DjangoModelFactory):
    """Factory pour le modèle TeamJoinRequest."""

    class Meta:
        model = "users.TeamJoinRequest"

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    status = "pending"


# ╔══════════════════════════════════════════════════════════════════╗
# ║                           GAMES                                  ║
# ╚══════════════════════════════════════════════════════════════════╝


class GameFactory(DjangoModelFactory):
    """Factory pour le modèle Game."""

    class Meta:
        model = "games.Game"

    room_code = factory.LazyFunction(lambda: uuid.uuid4().hex[:6].upper())
    host = factory.SubFactory(UserFactory)
    mode = "classique"
    status = "waiting"
    max_players = 8
    num_rounds = 10
    playlist_id = "12345"
    is_online = True
    is_public = False
    answer_mode = "mcq"
    round_duration = 30


class GamePlayerFactory(DjangoModelFactory):
    """Factory pour le modèle GamePlayer."""

    class Meta:
        model = "games.GamePlayer"

    game = factory.SubFactory(GameFactory)
    user = factory.SubFactory(UserFactory)
    score = 0
    consecutive_correct = 0
    is_connected = True


class GameRoundFactory(DjangoModelFactory):
    """Factory pour le modèle GameRound."""

    class Meta:
        model = "games.GameRound"

    game = factory.SubFactory(GameFactory)
    round_number = factory.Sequence(lambda n: n + 1)
    track_id = factory.Sequence(lambda n: f"track_{n}")
    track_name = factory.Sequence(lambda n: f"Song {n}")
    artist_name = factory.Sequence(lambda n: f"Artist {n}")
    correct_answer = factory.LazyAttribute(lambda obj: obj.track_name)
    options = factory.LazyFunction(lambda: ["Option A", "Option B", "Option C", "Option D"])
    preview_url = "https://example.com/preview.mp3"
    question_type = "guess_title"
    duration = 30


class GameAnswerFactory(DjangoModelFactory):
    """Factory pour le modèle GameAnswer."""

    class Meta:
        model = "games.GameAnswer"

    round = factory.SubFactory(GameRoundFactory)
    player = factory.SubFactory(GamePlayerFactory)
    answer = "Option A"
    is_correct = True
    points_earned = 100
    streak_bonus = 0
    response_time = 5.0


class GameInvitationFactory(DjangoModelFactory):
    """Factory pour le modèle GameInvitation."""

    class Meta:
        model = "games.GameInvitation"

    game = factory.SubFactory(GameFactory)
    sender = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
    status = "pending"


class KaraokeSongFactory(DjangoModelFactory):
    """Factory pour le modèle KaraokeSong."""

    class Meta:
        model = "games.KaraokeSong"

    title = factory.Sequence(lambda n: f"Karaoke Song {n}")
    artist = factory.Sequence(lambda n: f"Karaoke Artist {n}")
    youtube_video_id = factory.Sequence(lambda n: f"vid{n:010d}")
    is_active = True
    duration_ms = 180000


# ╔══════════════════════════════════════════════════════════════════╗
# ║                        ACHIEVEMENTS                              ║
# ╚══════════════════════════════════════════════════════════════════╝


class AchievementFactory(DjangoModelFactory):
    """Factory pour le modèle Achievement."""

    class Meta:
        model = "achievements.Achievement"

    name = factory.Sequence(lambda n: f"Achievement {n}")
    description = "Description de test"
    points = 10
    condition_type = "games_played"
    condition_value = 1


class UserAchievementFactory(DjangoModelFactory):
    """Factory pour le modèle UserAchievement."""

    class Meta:
        model = "achievements.UserAchievement"

    user = factory.SubFactory(UserFactory)
    achievement = factory.SubFactory(AchievementFactory)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                            SHOP                                  ║
# ╚══════════════════════════════════════════════════════════════════╝


class ShopItemFactory(DjangoModelFactory):
    """Factory pour le modèle ShopItem."""

    class Meta:
        model = "shop.ShopItem"

    name = factory.Sequence(lambda n: f"Item {n}")
    description = "Description de test"
    item_type = "bonus"
    bonus_type = "double_points"
    cost = 100
    is_available = True


class UserInventoryFactory(DjangoModelFactory):
    """Factory pour le modèle UserInventory."""

    class Meta:
        model = "shop.UserInventory"

    user = factory.SubFactory(UserFactory)
    item = factory.SubFactory(ShopItemFactory)
    quantity = 1


class GameBonusFactory(DjangoModelFactory):
    """Factory pour le modèle GameBonus."""

    class Meta:
        model = "shop.GameBonus"

    game = factory.SubFactory(GameFactory)
    player = factory.SubFactory(GamePlayerFactory)
    bonus_type = "double_points"
    is_used = False


# ╔══════════════════════════════════════════════════════════════════╗
# ║                       ADMINISTRATION                             ║
# ╚══════════════════════════════════════════════════════════════════╝


class SiteConfigurationFactory(DjangoModelFactory):
    """Factory pour le modèle SiteConfiguration (singleton)."""

    class Meta:
        model = "administration.SiteConfiguration"
        django_get_or_create = ("pk",)

    pk = 1
    maintenance_mode = False
    banner_enabled = False


class LegalPageFactory(DjangoModelFactory):
    """Factory pour le modèle LegalPage."""

    class Meta:
        model = "administration.LegalPage"

    page_type = "privacy"
    title = "Politique de confidentialité"
    content = "Contenu de test pour la page légale."
