"""Tests unitaires du modèle Game — introspection des champs et métadonnées."""

from unittest.mock import MagicMock, PropertyMock

from django.db import models

from apps.games.models import Game
from apps.games.models.enums import AnswerMode, GameMode, GameStatus, GuessTarget
from tests.base import BaseModelUnitTest


class TestGameModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle Game."""

    def get_model_class(self):
        return Game

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── room_code ───────────────────────────────────────────────────

    def test_room_code_max_length(self):
        self.assert_field_max_length(Game, "room_code", 6)

    def test_room_code_unique(self):
        self.assert_field_unique(Game, "room_code", True)

    # ── name ────────────────────────────────────────────────────────

    def test_name_max_length(self):
        self.assert_field_max_length(Game, "name", 100)

    def test_name_blank(self):
        self.assert_field_blank(Game, "name", True)

    # ── mode ────────────────────────────────────────────────────────

    def test_mode_max_length(self):
        self.assert_field_max_length(Game, "mode", 20)

    def test_mode_choices(self):
        self.assert_field_choices(Game, "mode", GameMode.choices)

    def test_mode_default(self):
        self.assert_field_default(Game, "mode", GameMode.CLASSIQUE)

    def test_mode_db_index(self):
        self.assert_field_db_index(Game, "mode", True)

    def test_game_mode_values(self):
        """Vérifie les 6 valeurs de GameMode."""
        assert GameMode.CLASSIQUE == "classique"
        assert GameMode.RAPIDE == "rapide"
        assert GameMode.GENERATION == "generation"
        assert GameMode.PAROLES == "paroles"
        assert GameMode.KARAOKE == "karaoke"
        assert GameMode.LENT == "mollo"

    # ── guess_target ────────────────────────────────────────────────

    def test_guess_target_max_length(self):
        self.assert_field_max_length(Game, "guess_target", 10)

    def test_guess_target_choices(self):
        self.assert_field_choices(Game, "guess_target", GuessTarget.choices)

    def test_guess_target_default(self):
        self.assert_field_default(Game, "guess_target", GuessTarget.TITLE)

    def test_guess_target_values(self):
        assert GuessTarget.ARTIST == "artist"
        assert GuessTarget.TITLE == "title"

    # ── status ──────────────────────────────────────────────────────

    def test_status_max_length(self):
        self.assert_field_max_length(Game, "status", 20)

    def test_status_choices(self):
        self.assert_field_choices(Game, "status", GameStatus.choices)

    def test_status_default(self):
        self.assert_field_default(Game, "status", GameStatus.WAITING)

    def test_status_db_index(self):
        self.assert_field_db_index(Game, "status", True)

    def test_game_status_values(self):
        assert GameStatus.WAITING == "waiting"
        assert GameStatus.IN_PROGRESS == "in_progress"
        assert GameStatus.FINISHED == "finished"
        assert GameStatus.CANCELLED == "cancelled"

    # ── answer_mode ─────────────────────────────────────────────────

    def test_answer_mode_max_length(self):
        self.assert_field_max_length(Game, "answer_mode", 10)

    def test_answer_mode_choices(self):
        self.assert_field_choices(Game, "answer_mode", AnswerMode.choices)

    def test_answer_mode_default(self):
        self.assert_field_default(Game, "answer_mode", AnswerMode.MCQ)

    def test_answer_mode_values(self):
        assert AnswerMode.MCQ == "mcq"
        assert AnswerMode.TEXT == "text"

    # ── Champs entiers ──────────────────────────────────────────────

    def test_max_players_default(self):
        self.assert_field_default(Game, "max_players", 8)

    def test_num_rounds_default(self):
        self.assert_field_default(Game, "num_rounds", 10)

    def test_round_duration_default(self):
        self.assert_field_default(Game, "round_duration", 30)

    def test_timer_start_round_default(self):
        self.assert_field_default(Game, "timer_start_round", 5)

    def test_score_display_duration_default(self):
        self.assert_field_default(Game, "score_display_duration", 10)

    def test_lyrics_words_count_default(self):
        self.assert_field_default(Game, "lyrics_words_count", 3)

    # ── Champs booléens ─────────────────────────────────────────────

    def test_is_online_default(self):
        self.assert_field_default(Game, "is_online", True)

    def test_is_public_default(self):
        self.assert_field_default(Game, "is_public", False)

    def test_is_public_db_index(self):
        self.assert_field_db_index(Game, "is_public", True)

    def test_is_party_mode_default(self):
        self.assert_field_default(Game, "is_party_mode", False)

    def test_bonuses_enabled_default(self):
        self.assert_field_default(Game, "bonuses_enabled", True)

    # ── Playlist ────────────────────────────────────────────────────

    def test_playlist_id_null(self):
        self.assert_field_null(Game, "playlist_id", True)

    def test_playlist_id_blank(self):
        self.assert_field_blank(Game, "playlist_id", True)

    def test_playlist_name_blank(self):
        self.assert_field_blank(Game, "playlist_name", True)

    def test_playlist_image_url_blank(self):
        self.assert_field_blank(Game, "playlist_image_url", True)

    # ── Karaoke ─────────────────────────────────────────────────────

    def test_karaoke_track_null(self):
        self.assert_field_null(Game, "karaoke_track", True)

    def test_karaoke_song_null(self):
        self.assert_field_null(Game, "karaoke_song", True)

    def test_karaoke_song_set_null(self):
        field = Game._meta.get_field("karaoke_song")
        assert field.remote_field.on_delete.__name__ == "SET_NULL"

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = Game._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_started_at_null(self):
        self.assert_field_null(Game, "started_at", True)

    def test_finished_at_null(self):
        self.assert_field_null(Game, "finished_at", True)

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("partie", "parties")

    def test_ordering(self):
        self.assert_ordering(Game, ["-created_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_contains_room_code(self):
        game = MagicMock(spec=Game)
        game.room_code = "ABC123"
        game.get_mode_display = MagicMock(return_value="Classique")
        result = Game.__str__(game)
        assert "ABC123" in result
        assert "Classique" in result

    # ── competitive_players ─────────────────────────────────────────

    def test_competitive_players_normal(self):
        """En mode normal, tous les joueurs sont éligibles."""
        game = MagicMock(spec=Game)
        game.is_party_mode = False
        mock_qs = MagicMock()
        game.players.all.return_value = mock_qs
        result = Game.competitive_players(game)
        assert result == mock_qs
        mock_qs.exclude.assert_not_called()

    def test_competitive_players_party_mode(self):
        """En mode soirée, l'hôte est exclu."""
        game = MagicMock(spec=Game)
        game.is_party_mode = True
        game.host = MagicMock()
        mock_qs = MagicMock()
        game.players.all.return_value = mock_qs
        Game.competitive_players(game)
        mock_qs.exclude.assert_called_once_with(user=game.host)
