"""
Services for game logic.
Uses Deezer API for music content (30-second MP3 previews).
"""
import random
import logging
import re
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from .models import Game, GamePlayer, GameRound, GameAnswer, GameStatus, GameMode
from apps.playlists.deezer_service import deezer_service, DeezerAPIError
from apps.achievements.services import achievement_service
from .lyrics_service import get_lyrics, create_lyrics_question

logger = logging.getLogger(__name__)


# ─── Mode → default duration & question_type mapping ─────────────────────────
MODE_CONFIG = {
    GameMode.QUIZ_4_ANSWERS: {
        'duration': 30,
        'question_type': 'guess_title',
    },
    GameMode.BLIND_TEST_INVERSE: {
        'duration': 30,
        'question_type': 'blind_inverse',
    },
    GameMode.GUESS_YEAR: {
        'duration': 30,
        'question_type': 'guess_year',
    },
    GameMode.INTRO: {
        'duration': 5,
        'question_type': 'intro',
    },
    GameMode.LYRICS: {
        'duration': 30,
        'question_type': 'lyrics',
    },
}


class QuestionGeneratorService:
    """Service to generate quiz questions from Deezer music playlists."""

    QUESTION_TYPES = ['guess_title', 'guess_artist', 'blind_inverse', 'guess_year', 'intro', 'lyrics']

    def __init__(self):
        self.deezer = deezer_service

    # ─── Public entry point ──────────────────────────────────────────

    def generate_questions(
        self,
        playlist_id: str,
        num_questions: int = 10,
        question_type: str = 'guess_title',
        game_mode: str = 'quiz_4',
        user=None,
    ) -> List[Dict]:
        """
        Generate quiz questions from a Deezer playlist.

        Args:
            playlist_id: Deezer playlist ID
            num_questions: Number of questions to generate
            question_type: Type of question
            game_mode: The game mode (determines generator)
            user: Django user (unused, kept for compat)

        Returns:
            List of question dictionaries
        """
        tracks = self._fetch_tracks(playlist_id, limit=50)

        random.shuffle(tracks)
        selected_tracks = tracks[:min(num_questions * 2, len(tracks))]  # extra buffer

        questions: List[Dict] = []

        for track in selected_tracks:
            if len(questions) >= num_questions:
                break

            question = self._generate_for_mode(game_mode, track, tracks)
            if question:
                questions.append(question)

        return questions

    # ─── Track fetching (shared) ─────────────────────────────────────

    def _fetch_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """Fetch tracks from Deezer playlist with fallback."""
        try:
            logger.info("Fetching tracks from Deezer playlist %s", playlist_id)
            tracks = self.deezer.get_playlist_tracks(playlist_id, limit=limit)
        except DeezerAPIError as e:
            logger.error("Failed to get tracks from Deezer playlist %s: %s", playlist_id, e)
            raise ValueError(f"Erreur lors de l'accès à la playlist Deezer: {e}")

        if not tracks or len(tracks) < 4:
            found = len(tracks) if tracks else 0
            logger.warning("Deezer playlist %s returned %d tracks, attempting fallback", playlist_id, found)

            try:
                meta = self.deezer.get_playlist(playlist_id)
                query = meta['name'] if meta and meta.get('name') else playlist_id
            except Exception:
                query = playlist_id

            try:
                fallback = self.deezer.search_music_videos(query, limit=limit)
            except Exception as e:
                logger.error("Fallback search failed: %s", e)
                fallback = []

            if fallback and len(fallback) >= 4:
                tracks = fallback
            else:
                raise ValueError(
                    f"La playlist ne contient pas assez de morceaux "
                    f"({found} trouvés, minimum 4 requis)."
                )

        return tracks

    # ─── Mode dispatcher ─────────────────────────────────────────────

    def _generate_for_mode(self, game_mode: str, track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Route to the correct question generator based on game mode."""
        if game_mode == GameMode.BLIND_TEST_INVERSE:
            return self._generate_blind_inverse_question(track, all_tracks)
        elif game_mode == GameMode.GUESS_YEAR:
            return self._generate_year_question(track)
        elif game_mode == GameMode.INTRO:
            return self._generate_intro_question(track, all_tracks)
        elif game_mode == GameMode.LYRICS:
            return self._generate_lyrics_question(track, all_tracks)
        else:
            # Default: quiz_4
            return self._generate_guess_title_question(track, all_tracks)

    # ─── Quiz 4 (default) ────────────────────────────────────────────

    def _generate_guess_title_question(self, correct_track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Generate a 'guess the title' question."""
        correct_answer = correct_track['name']
        wrong_answers = self._pick_wrong_answers(correct_track, all_tracks, key='name', count=3)
        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        return {
            'track_id': correct_track['youtube_id'],
            'track_name': correct_track['name'],
            'artist_name': ', '.join(correct_track['artists']),
            'preview_url': correct_track.get('preview_url'),
            'album_image': correct_track.get('album_image'),
            'question_type': 'guess_title',
            'question_text': 'Quel est le titre de ce morceau ?',
            'correct_answer': correct_answer,
            'options': options,
            'extra_data': {},
        }

    def _generate_guess_artist_question(self, correct_track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Generate a 'guess the artist' question."""
        correct_answer = ', '.join(correct_track['artists'])
        other_tracks = [t for t in all_tracks if t['youtube_id'] != correct_track['youtube_id']]
        random.shuffle(other_tracks)

        wrong_answers = []
        for track in other_tracks:
            artist = ', '.join(track['artists'])
            if artist != correct_answer and artist not in wrong_answers:
                wrong_answers.append(artist)
            if len(wrong_answers) >= 3:
                break

        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        return {
            'track_id': correct_track['youtube_id'],
            'track_name': correct_track['name'],
            'artist_name': correct_answer,
            'preview_url': correct_track.get('preview_url'),
            'album_image': correct_track.get('album_image'),
            'question_type': 'guess_artist',
            'question_text': 'Qui interprète ce morceau ?',
            'correct_answer': correct_answer,
            'options': options,
            'extra_data': {},
        }

    # ─── Blind Test Inversé ──────────────────────────────────────────

    def _generate_blind_inverse_question(self, correct_track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Artist is given prominently, player guesses the title."""
        correct_answer = correct_track['name']
        wrong_answers = self._pick_wrong_answers(correct_track, all_tracks, key='name', count=3)
        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        artist = ', '.join(correct_track['artists'])
        return {
            'track_id': correct_track['youtube_id'],
            'track_name': correct_track['name'],
            'artist_name': artist,
            'preview_url': correct_track.get('preview_url'),
            'album_image': correct_track.get('album_image'),
            'question_type': 'blind_inverse',
            'question_text': f"L'artiste est {artist}. Quel est le titre ?",
            'correct_answer': correct_answer,
            'options': options,
            'extra_data': {},
        }

    # ─── Année de Sortie ─────────────────────────────────────────────

    def _generate_year_question(self, track: Dict) -> Optional[Dict]:
        """Player guesses the release year (±2 tolerance)."""
        track_id = track['youtube_id']

        # Get detailed info including release_date
        details = self.deezer.get_track_details(track_id)
        if not details or not details.get('release_date'):
            return None

        release_date = details['release_date']  # "YYYY-MM-DD"
        try:
            year = int(release_date[:4])
        except (ValueError, IndexError):
            return None

        if year < 1950 or year > 2030:
            return None

        artist = ', '.join(track['artists'])
        return {
            'track_id': track_id,
            'track_name': track['name'],
            'artist_name': artist,
            'preview_url': track.get('preview_url'),
            'album_image': track.get('album_image'),
            'question_type': 'guess_year',
            'question_text': f'En quelle année est sorti « {track["name"]} » de {artist} ?',
            'correct_answer': str(year),
            'options': [],  # No MCQ — free numeric input
            'extra_data': {
                'release_date': release_date,
                'year': year,
                'tolerance': 2,
            },
        }

    # ─── Intro (5 seconds) ───────────────────────────────────────────

    def _generate_intro_question(self, correct_track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Same as guess_title but only 5 seconds of audio."""
        correct_answer = correct_track['name']
        wrong_answers = self._pick_wrong_answers(correct_track, all_tracks, key='name', count=3)
        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        return {
            'track_id': correct_track['youtube_id'],
            'track_name': correct_track['name'],
            'artist_name': ', '.join(correct_track['artists']),
            'preview_url': correct_track.get('preview_url'),
            'album_image': correct_track.get('album_image'),
            'question_type': 'intro',
            'question_text': 'Reconnaissez ce morceau en 5 secondes !',
            'correct_answer': correct_answer,
            'options': options,
            'extra_data': {'audio_duration': 5},
        }

    # ─── Lyrics ──────────────────────────────────────────────────────

    def _generate_lyrics_question(self, track: Dict, all_tracks: List[Dict]) -> Optional[Dict]:
        """Fetch lyrics, extract a line, blank out a word, 4 MCQ options."""
        artist = ', '.join(track['artists'])
        lyrics = get_lyrics(artist, track['name'])

        if not lyrics:
            # Fallback: use a standard guess_title question
            return self._generate_guess_title_question(track, all_tracks)

        # Collect extra words from other track titles for wrong options
        extra_words = []
        for t in all_tracks:
            extra_words.extend(re.findall(r'[a-zA-ZÀ-ÿ\'-]{3,}', t['name']))

        result = create_lyrics_question(lyrics, extra_words)
        if not result:
            return self._generate_guess_title_question(track, all_tracks)

        snippet, correct_word, options = result

        return {
            'track_id': track['youtube_id'],
            'track_name': track['name'],
            'artist_name': artist,
            'preview_url': track.get('preview_url'),
            'album_image': track.get('album_image'),
            'question_type': 'lyrics',
            'question_text': f'Complétez les paroles de « {track["name"]} » :',
            'correct_answer': correct_word,
            'options': options,
            'extra_data': {
                'lyrics_snippet': snippet,
            },
        }

    # ─── Helpers ─────────────────────────────────────────────────────

    def _pick_wrong_answers(
        self, correct_track: Dict, all_tracks: List[Dict], key: str = 'name', count: int = 3
    ) -> List[str]:
        """Pick distinct wrong answers from the track pool."""
        correct_val = correct_track[key]
        other = [t for t in all_tracks if t['youtube_id'] != correct_track['youtube_id']]
        random.shuffle(other)

        wrong = []
        for t in other:
            val = t[key] if isinstance(t[key], str) else ', '.join(t[key])
            if val != correct_val and val not in wrong:
                wrong.append(val)
            if len(wrong) >= count:
                break
        return wrong


class GameService:
    """Service to manage game flow and logic."""

    def __init__(self):
        self.question_generator = QuestionGeneratorService()

    @transaction.atomic
    def start_game(self, game: Game) -> Tuple[Game, List[GameRound]]:
        """Start a game and generate rounds from a Deezer playlist."""
        if game.status != GameStatus.WAITING:
            raise ValueError("Game is not in waiting status")

        if not game.playlist_id:
            raise ValueError("Game must have a playlist")

        num_rounds = game.num_rounds or 10
        mode = game.mode
        config = MODE_CONFIG.get(mode, MODE_CONFIG[GameMode.QUIZ_4_ANSWERS])

        questions = self.question_generator.generate_questions(
            game.playlist_id,
            num_questions=num_rounds,
            question_type=config['question_type'],
            game_mode=mode,
            user=game.host,
        )

        if not questions:
            raise ValueError("Failed to generate questions from playlist")

        rounds = []
        for i, q in enumerate(questions, start=1):
            round_obj = GameRound.objects.create(
                game=game,
                round_number=i,
                track_id=q['track_id'],
                track_name=q['track_name'],
                artist_name=q['artist_name'],
                correct_answer=q['correct_answer'],
                options=q['options'],
                preview_url=q.get('preview_url', ''),
                question_type=q.get('question_type', config['question_type']),
                question_text=q.get('question_text', ''),
                extra_data=q.get('extra_data', {}),
                duration=config['duration'],
            )
            rounds.append(round_obj)

        game.status = GameStatus.IN_PROGRESS
        game.started_at = timezone.now()
        game.save()

        if rounds:
            rounds[0].started_at = timezone.now()
            rounds[0].save()

        return game, rounds

    def get_current_round(self, game: Game) -> Optional[GameRound]:
        return game.rounds.filter(started_at__isnull=False, ended_at__isnull=True).order_by('round_number').first()

    def get_next_round(self, game: Game) -> Optional[GameRound]:
        return game.rounds.filter(started_at__isnull=True).order_by('round_number').first()

    def start_round(self, round_obj: GameRound) -> GameRound:
        round_obj.started_at = timezone.now()
        round_obj.save()
        return round_obj

    @transaction.atomic
    def end_round(self, round_obj: GameRound) -> GameRound:
        round_obj.ended_at = timezone.now()
        round_obj.save()
        return round_obj

    # ─── Scoring ─────────────────────────────────────────────────────

    def check_answer(self, game_mode: str, answer: str, correct_answer: str, extra_data: dict | None = None) -> Tuple[bool, float]:
        """
        Check answer and return (is_correct, accuracy_factor).

        accuracy_factor: 1.0 = exact, 0.6 = ±1 year, 0.3 = ±2 years, 0.0 = wrong
        For non-year modes: 1.0 or 0.0.
        """
        if game_mode == GameMode.GUESS_YEAR:
            try:
                given = int(answer)
                correct = int(correct_answer)
            except (ValueError, TypeError):
                return False, 0.0

            diff = abs(given - correct)
            if diff == 0:
                return True, 1.0
            elif diff == 1:
                return True, 0.6
            elif diff == 2:
                return True, 0.3
            else:
                return False, 0.0
        else:
            is_correct = answer == correct_answer
            return is_correct, 1.0 if is_correct else 0.0

    def calculate_score(self, accuracy_factor: float, response_time: float, max_time: int = 30) -> int:
        """Calculate base points (Option C — Linear + Rank).

        Correct: (100 - response_time * 3) * accuracy_factor, min 10 when correct.
        """
        if accuracy_factor <= 0.0:
            return 0
        raw = max(10, 100 - int(response_time * 3))
        return max(5, int(raw * accuracy_factor))

    @transaction.atomic
    def submit_answer(self, player: GamePlayer, round_obj: GameRound, answer: str, response_time: float) -> GameAnswer:
        """Submit and score a player's answer."""
        game_mode = round_obj.game.mode
        is_correct, accuracy_factor = self.check_answer(
            game_mode, answer, round_obj.correct_answer, round_obj.extra_data
        )
        points = self.calculate_score(accuracy_factor, response_time, round_obj.duration)

        # Rank bonus: +10 for 1st correct, +5 for 2nd, +2 for 3rd
        rank_bonus = 0
        if is_correct:
            correct_before = GameAnswer.objects.filter(round=round_obj, is_correct=True).count()
            if correct_before == 0:
                rank_bonus = 10
            elif correct_before == 1:
                rank_bonus = 5
            elif correct_before == 2:
                rank_bonus = 2
            points += rank_bonus

        game_answer = GameAnswer.objects.create(
            round=round_obj,
            player=player,
            answer=answer,
            is_correct=is_correct,
            points_earned=points,
            response_time=response_time,
        )

        player.score += points
        player.save()
        return game_answer

    @transaction.atomic
    def finish_game(self, game: Game) -> Game:
        """Finish a game and calculate final rankings."""
        game.status = GameStatus.FINISHED
        game.finished_at = timezone.now()
        game.save()

        players = game.players.order_by('-score')
        total_rounds = game.rounds.count()

        for rank, player in enumerate(players, start=1):
            player.rank = rank
            player.save()

            user = player.user
            user.total_games_played += 1
            user.total_points += player.score
            if rank == 1:
                user.total_wins += 1
            user.save()

            correct_answers = GameAnswer.objects.filter(
                player=player, round__game=game, is_correct=True,
            ).count()
            perfect_game = total_rounds > 0 and correct_answers == total_rounds

            round_data = {'perfect_game': perfect_game}
            achievement_service.check_and_award(user, game=game, round_data=round_data)

        return game


# Singleton instances
question_generator_service = QuestionGeneratorService()
game_service = GameService()
