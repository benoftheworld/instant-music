"""Tests unitaires du service QuestionGeneratorService."""

from unittest.mock import MagicMock, patch

import pytest

from tests.base import BaseServiceUnitTest


class TestQuestionGeneratorFetchTracks(BaseServiceUnitTest):
    """Vérifie _fetch_tracks avec succès et fallback."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    def _make_svc(self):
        from apps.games.services.question_generator import QuestionGeneratorService

        return QuestionGeneratorService()

    @patch("apps.games.services.question_generator.deezer_service")
    def test_fetch_tracks_success(self, mock_deezer):
        mock_deezer.get_playlist_tracks.return_value = [
            {"track_id": i, "name": f"T{i}", "artists": [f"A{i}"]} for i in range(10)
        ]
        svc = self._make_svc()
        svc.deezer = mock_deezer
        tracks = svc._fetch_tracks("123", limit=50)
        assert len(tracks) == 10

    @patch("apps.games.services.question_generator.deezer_service")
    def test_fetch_tracks_fallback_on_few_tracks(self, mock_deezer):
        mock_deezer.get_playlist_tracks.return_value = [{"track_id": 1}]
        mock_deezer.get_playlist.return_value = {"name": "My Playlist"}
        mock_deezer.search_music_videos.return_value = [
            {"track_id": i} for i in range(10)
        ]
        svc = self._make_svc()
        svc.deezer = mock_deezer
        tracks = svc._fetch_tracks("123")
        assert len(tracks) == 10

    @patch("apps.games.services.question_generator.deezer_service")
    def test_fetch_tracks_error(self, mock_deezer):
        from apps.playlists.deezer_service import DeezerAPIError

        mock_deezer.get_playlist_tracks.side_effect = DeezerAPIError("fail")
        svc = self._make_svc()
        svc.deezer = mock_deezer
        with pytest.raises(ValueError):
            svc._fetch_tracks("123")

    @patch("apps.games.services.question_generator.deezer_service")
    def test_fetch_tracks_fallback_not_enough(self, mock_deezer):
        mock_deezer.get_playlist_tracks.return_value = [{"track_id": 1}]
        mock_deezer.get_playlist.return_value = {"name": "PL"}
        mock_deezer.search_music_videos.return_value = [{"track_id": 1}]
        svc = self._make_svc()
        svc.deezer = mock_deezer
        with pytest.raises(ValueError):
            svc._fetch_tracks("123")


class TestQuestionGeneratorGenerateForMode(BaseServiceUnitTest):
    """Vérifie _generate_for_mode route vers le bon générateur."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    def _make_svc(self):
        from apps.games.services.question_generator import QuestionGeneratorService

        return QuestionGeneratorService()

    def _make_track(self, **kwargs):
        base = {
            "track_id": "1",
            "name": "Song",
            "artists": ["Artist"],
            "preview_url": "http://x.mp3",
            "album_image": "http://x.jpg",
        }
        base.update(kwargs)
        return base

    def _make_tracks(self, n=5):
        return [
            self._make_track(track_id=str(i), name=f"Song{i}", artists=[f"Artist{i}"])
            for i in range(n)
        ]

    @patch.object(
        __import__(
            "apps.games.services.question_generator",
            fromlist=["QuestionGeneratorService"],
        ).QuestionGeneratorService,
        "_generate_guess_title_question",
        return_value={"q": "title"},
    )
    def test_classique_title(self, mock_gen):
        svc = self._make_svc()
        track = self._make_track()
        result = svc._generate_for_mode(
            "classique", track, [track], guess_target="title"
        )
        assert result is not None

    @patch.object(
        __import__(
            "apps.games.services.question_generator",
            fromlist=["QuestionGeneratorService"],
        ).QuestionGeneratorService,
        "_generate_guess_artist_question",
        return_value={"q": "artist"},
    )
    def test_classique_artist(self, mock_gen):
        svc = self._make_svc()
        track = self._make_track()
        result = svc._generate_for_mode(
            "classique", track, [track], guess_target="artist"
        )
        assert result is not None

    def test_generation_mode(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_year_question", return_value={"q": "year"}
        ) as m:
            result = svc._generate_for_mode("generation", track, [track])
            m.assert_called_once()
            assert result is not None

    def test_paroles_mode(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_lyrics_question", return_value={"q": "lyrics"}
        ) as m:
            svc._generate_for_mode("paroles", track, [track])
            m.assert_called_once()

    def test_karaoke_mode(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_karaoke_question", return_value={"q": "k"}
        ) as m:
            svc._generate_for_mode("karaoke", track, [track])
            m.assert_called_once()

    def test_rapide_adds_audio_duration(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_guess_title_question", return_value={"extra_data": {}}
        ):
            result = svc._generate_for_mode(
                "rapide", track, [track], guess_target="title"
            )
            assert result["extra_data"]["audio_duration"] == 3

    def test_lent_adds_slow_effect(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_guess_title_question", return_value={"extra_data": {}}
        ):
            result = svc._generate_for_mode(
                "mollo", track, [track], guess_target="title"
            )
            assert result["extra_data"]["audio_effect"] == "slow"

    def test_unknown_mode_defaults_title(self):
        svc = self._make_svc()
        track = self._make_track()
        with patch.object(
            svc, "_generate_guess_title_question", return_value={"q": "t"}
        ) as m:
            svc._generate_for_mode("unknown_mode", track, [track])
            m.assert_called_once()


class TestGenerateGuessQuestions(BaseServiceUnitTest):
    """Vérifie la génération des questions guess_title et guess_artist."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    def _make_svc(self):
        from apps.games.services.question_generator import QuestionGeneratorService

        return QuestionGeneratorService()

    def _make_tracks(self, n=5):
        return [
            {
                "track_id": str(i),
                "name": f"Song{i}",
                "artists": [f"Artist{i}"],
                "preview_url": f"http://x{i}.mp3",
                "album_image": f"http://x{i}.jpg",
            }
            for i in range(n)
        ]

    def test_guess_title_success(self):
        svc = self._make_svc()
        tracks = self._make_tracks(5)
        result = svc._generate_guess_title_question(tracks[0], tracks)
        assert result is not None
        assert result["question_type"] == "guess_title"
        assert result["correct_answer"] == "Song0"
        assert len(result["options"]) == 4

    def test_guess_title_not_enough_wrong_answers(self):
        svc = self._make_svc()
        tracks = self._make_tracks(2)
        result = svc._generate_guess_title_question(tracks[0], tracks)
        assert result is None

    def test_guess_artist_success(self):
        svc = self._make_svc()
        tracks = self._make_tracks(5)
        result = svc._generate_guess_artist_question(tracks[0], tracks)
        assert result is not None
        assert result["question_type"] == "guess_artist"
        assert len(result["options"]) == 4

    def test_guess_artist_not_enough_wrong(self):
        svc = self._make_svc()
        tracks = self._make_tracks(2)
        result = svc._generate_guess_artist_question(tracks[0], tracks)
        assert result is None

    def test_pick_wrong_answers(self):
        svc = self._make_svc()
        tracks = self._make_tracks(5)
        wrong = svc._pick_wrong_answers(tracks[0], tracks, key="name", count=3)
        assert len(wrong) == 3
        assert "Song0" not in wrong


class TestGenerateYearQuestion(BaseServiceUnitTest):
    """Vérifie la génération des questions de type year/generation."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    def _make_svc(self):
        from apps.games.services.question_generator import QuestionGeneratorService

        return QuestionGeneratorService()

    @patch("apps.games.services.question_generator.deezer_service")
    def test_year_question_success(self, mock_deezer):
        mock_deezer.get_track_details.return_value = {"release_date": "2005-06-01"}
        svc = self._make_svc()
        svc.deezer = mock_deezer
        track = {
            "track_id": "1",
            "name": "Song",
            "artists": ["Artist"],
            "preview_url": "url",
            "album_image": "img",
        }
        with patch.object(svc, "_get_musicbrainz_year", return_value=None):
            result = svc._generate_year_question(track)
        assert result is not None
        assert result["correct_answer"] == "2005"
        assert len(result["options"]) == 4

    @patch("apps.games.services.question_generator.deezer_service")
    def test_year_question_no_details(self, mock_deezer):
        mock_deezer.get_track_details.return_value = None
        svc = self._make_svc()
        svc.deezer = mock_deezer
        track = {"track_id": "1", "name": "Song", "artists": ["Artist"]}
        result = svc._generate_year_question(track)
        assert result is None

    @patch("apps.games.services.question_generator.deezer_service")
    def test_year_question_invalid_date(self, mock_deezer):
        mock_deezer.get_track_details.return_value = {"release_date": "bad"}
        svc = self._make_svc()
        svc.deezer = mock_deezer
        track = {"track_id": "1", "name": "Song", "artists": ["Artist"]}
        result = svc._generate_year_question(track)
        assert result is None

    @patch("apps.games.services.question_generator.deezer_service")
    def test_year_question_musicbrainz_correction(self, mock_deezer):
        mock_deezer.get_track_details.return_value = {"release_date": "2010-01-01"}
        svc = self._make_svc()
        svc.deezer = mock_deezer
        track = {
            "track_id": "1",
            "name": "Song",
            "artists": ["Artist"],
            "preview_url": "url",
            "album_image": "img",
        }
        with patch.object(svc, "_get_musicbrainz_year", return_value=2005):
            result = svc._generate_year_question(track)
        assert result is not None
        assert result["correct_answer"] == "2005"


class TestMusicBrainzYear(BaseServiceUnitTest):
    """Vérifie _get_musicbrainz_year."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    @patch("apps.games.services.question_generator.cache")
    @patch("apps.games.services.question_generator.requests.get")
    def test_cached_result(self, mock_get, mock_cache):
        mock_cache.get.return_value = 2005
        from apps.games.services.question_generator import QuestionGeneratorService

        result = QuestionGeneratorService._get_musicbrainz_year("Artist", "Song")
        assert result == 2005
        mock_get.assert_not_called()

    @patch("apps.games.services.question_generator.cache")
    @patch("apps.games.services.question_generator.requests.get")
    def test_api_success(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "recordings": [
                {"score": 90, "first-release-date": "2003-05-01"},
                {"score": 95, "first-release-date": "2005-01-01"},
            ]
        }
        mock_get.return_value = mock_resp
        from apps.games.services.question_generator import QuestionGeneratorService

        result = QuestionGeneratorService._get_musicbrainz_year("Artist", "Song")
        assert result == 2003

    @patch("apps.games.services.question_generator.cache")
    @patch("apps.games.services.question_generator.requests.get")
    def test_api_failure(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_get.side_effect = Exception("timeout")
        from apps.games.services.question_generator import QuestionGeneratorService

        result = QuestionGeneratorService._get_musicbrainz_year("Artist", "Song")
        assert result is None

    @patch("apps.games.services.question_generator.cache")
    @patch("apps.games.services.question_generator.requests.get")
    def test_low_score_ignored(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "recordings": [{"score": 50, "first-release-date": "2003-01-01"}]
        }
        mock_get.return_value = mock_resp
        from apps.games.services.question_generator import QuestionGeneratorService

        result = QuestionGeneratorService._get_musicbrainz_year("Artist", "Song")
        assert result is None


class TestGenerateLyricsQuestion(BaseServiceUnitTest):
    """Vérifie _generate_lyrics_question."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    @patch("apps.games.services.question_generator.create_lyrics_question")
    @patch("apps.games.services.question_generator.get_lyrics")
    def test_success(self, mock_gl, mock_clq):
        mock_gl.return_value = "Some lyrics text"
        mock_clq.return_value = (
            "snippet ___",
            "correct",
            ["correct", "w1", "w2", "w3"],
        )
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        track = {
            "track_id": "1",
            "name": "Song",
            "artists": ["Artist"],
            "preview_url": "url",
            "album_image": "img",
        }
        result = svc._generate_lyrics_question(track, [track])
        assert result is not None
        assert result["question_type"] == "lyrics"

    @patch("apps.games.services.question_generator.get_lyrics")
    def test_no_lyrics(self, mock_gl):
        mock_gl.return_value = None
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        track = {"track_id": "1", "name": "Song", "artists": ["Artist"]}
        result = svc._generate_lyrics_question(track, [track])
        assert result is None


class TestGenerateKaraokeQuestion(BaseServiceUnitTest):
    """Vérifie _generate_karaoke_question."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    @patch("apps.games.services.question_generator.youtube_service")
    @patch("apps.games.services.question_generator.get_synced_lyrics")
    def test_success(self, mock_synced, mock_yt):
        mock_synced.return_value = ([{"time_ms": 0, "text": "la la"}], None)
        mock_yt.search_music_videos.return_value = [
            {"track_id": "yt_123", "duration_ms": 180000}
        ]
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        track = {
            "track_id": "1",
            "name": "Song",
            "artists": ["Artist"],
            "preview_url": "url",
            "album_image": "img",
        }
        result = svc._generate_karaoke_question(track, [track])
        assert result is not None
        assert result["question_type"] == "karaoke"
        assert result["extra_data"]["youtube_video_id"] == "yt_123"

    @patch("apps.games.services.question_generator.get_synced_lyrics")
    def test_no_synced_lyrics(self, mock_synced):
        mock_synced.return_value = (None, None)
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        track = {"track_id": "1", "name": "Song", "artists": ["Artist"]}
        result = svc._generate_karaoke_question(track, [track])
        assert result is None

    @patch("apps.games.services.question_generator.youtube_service")
    @patch("apps.games.services.question_generator.get_synced_lyrics")
    def test_no_youtube_video(self, mock_synced, mock_yt):
        mock_synced.return_value = ([{"time_ms": 0, "text": "la"}], None)
        from apps.playlists.youtube_service import YouTubeAPIError

        mock_yt.search_music_videos.side_effect = YouTubeAPIError("fail")
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        track = {"track_id": "1", "name": "Song", "artists": ["Artist"]}
        result = svc._generate_karaoke_question(track, [track])
        assert result is None


class TestGenerateQuestions(BaseServiceUnitTest):
    """Vérifie generate_questions (point d'entrée principal)."""

    def get_service_module(self):
        from apps.games.services import question_generator

        return question_generator

    def test_generate_questions(self):
        from apps.games.services.question_generator import QuestionGeneratorService

        svc = QuestionGeneratorService()
        tracks = [
            {
                "track_id": str(i),
                "name": f"Song{i}",
                "artists": [f"A{i}"],
                "preview_url": f"u{i}",
                "album_image": f"img{i}",
            }
            for i in range(10)
        ]
        with (
            patch.object(svc, "_fetch_tracks", return_value=tracks),
            patch.object(
                svc, "_generate_for_mode", side_effect=lambda *a, **kw: {"q": "ok"}
            ),
        ):
            result = svc.generate_questions("123", num_questions=5)
        assert len(result) == 5
