"""
Services for game logic.
Uses Deezer API for music content (30-second MP3 previews).
"""
import random
import logging
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from .models import Game, GamePlayer, GameRound, GameAnswer, GameStatus
from apps.playlists.deezer_service import deezer_service, DeezerAPIError
from apps.achievements.services import achievement_service

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """Service to generate quiz questions from Deezer music playlists."""
    
    QUESTION_TYPES = ['guess_title', 'guess_artist']
    
    def __init__(self):
        self.deezer = deezer_service
    
    def generate_questions(
        self,
        playlist_id: str,
        num_questions: int = 10,
        question_type: str = 'guess_title',
        user=None
    ) -> List[Dict]:
        """
        Generate quiz questions from a Deezer playlist.
        
        Args:
            playlist_id: Deezer playlist ID
            num_questions: Number of questions to generate
            question_type: Type of question ('guess_title' or 'guess_artist')
            user: Django user (unused, kept for interface compat)
        
        Returns:
            List of question dictionaries
        """
        try:
            logger.info("Fetching tracks from Deezer playlist %s", playlist_id)
            tracks = self.deezer.get_playlist_tracks(playlist_id, limit=50)
        except DeezerAPIError as e:
            error_msg = str(e)
            logger.error("Failed to get tracks from Deezer playlist %s: %s", playlist_id, error_msg)
            raise ValueError(f"Erreur lors de l'accès à la playlist Deezer: {error_msg}")
        
        # If playlist provides too few tracks, try a fallback search by playlist title
        if not tracks or len(tracks) < 4:
            found = len(tracks) if tracks else 0
            logger.warning("Deezer playlist %s returned %d tracks, attempting fallback search", playlist_id, found)

            # Try to retrieve playlist metadata to use its title as a search query
            try:
                playlist_meta = self.deezer.get_playlist(playlist_id)
                playlist_query = None
                if playlist_meta and playlist_meta.get('name'):
                    playlist_query = playlist_meta['name']
            except Exception:
                playlist_query = None

            # Use playlist title or the playlist id as a fallback search query
            search_query = playlist_query or playlist_id
            try:
                fallback_tracks = self.deezer.search_music_videos(search_query, limit=50)
            except Exception as e:
                logger.error("Fallback search failed for %s: %s", search_query, e)
                fallback_tracks = []

            if fallback_tracks and len(fallback_tracks) >= 4:
                logger.info("Fallback search returned %d tracks for %s", len(fallback_tracks), search_query)
                tracks = fallback_tracks
            else:
                logger.warning("Fallback search also insufficient (%d) for %s", len(fallback_tracks) if fallback_tracks else 0, search_query)
                raise ValueError(
                    f"La playlist ne contient pas assez de morceaux "
                    f"({found} trouvés, minimum 4 requis)."
                )
        
        # Shuffle and select tracks for questions
        random.shuffle(tracks)
        selected_tracks = tracks[:min(num_questions, len(tracks))]
        
        questions = []
        for track in selected_tracks:
            if question_type == 'guess_title':
                question = self._generate_guess_title_question(track, tracks)
            elif question_type == 'guess_artist':
                question = self._generate_guess_artist_question(track, tracks)
            else:
                question = self._generate_guess_title_question(track, tracks)
            
            if question:
                questions.append(question)
        
        return questions
    
    def _generate_guess_title_question(
        self,
        correct_track: Dict,
        all_tracks: List[Dict]
    ) -> Optional[Dict]:
        """Generate a 'guess the title' question."""
        correct_answer = correct_track['name']
        
        other_tracks = [t for t in all_tracks if t['youtube_id'] != correct_track['youtube_id']]
        random.shuffle(other_tracks)
        
        wrong_answers = []
        for track in other_tracks:
            if track['name'] != correct_answer and track['name'] not in wrong_answers:
                wrong_answers.append(track['name'])
            if len(wrong_answers) >= 3:
                break
        
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
        }
    
    def _generate_guess_artist_question(
        self,
        correct_track: Dict,
        all_tracks: List[Dict]
    ) -> Optional[Dict]:
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
        }


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
        questions = self.question_generator.generate_questions(
            game.playlist_id,
            num_questions=num_rounds,
            user=game.host
        )
        
        if not questions:
            raise ValueError("Failed to generate questions from playlist")
        
        rounds = []
        for i, question in enumerate(questions, start=1):
            round_obj = GameRound.objects.create(
                game=game,
                round_number=i,
                track_id=question['track_id'],
                track_name=question['track_name'],
                artist_name=question['artist_name'],
                correct_answer=question['correct_answer'],
                options=question['options'],
                preview_url=question.get('preview_url', ''),
                duration=30,
            )
            rounds.append(round_obj)
        
        game.status = GameStatus.IN_PROGRESS
        game.started_at = timezone.now()
        game.save()
        
        # Start the first round
        if rounds:
            rounds[0].started_at = timezone.now()
            rounds[0].save()
        
        return game, rounds
    
    def get_current_round(self, game: Game) -> Optional[GameRound]:
        """Get the current active round for a game (started but not ended)."""
        return game.rounds.filter(
            started_at__isnull=False,
            ended_at__isnull=True
        ).order_by('round_number').first()
    
    def get_next_round(self, game: Game) -> Optional[GameRound]:
        """Get the next round to play (not yet started)."""
        return game.rounds.filter(
            started_at__isnull=True
        ).order_by('round_number').first()
    
    def start_round(self, round_obj: GameRound) -> GameRound:
        """Mark a round as started."""
        round_obj.started_at = timezone.now()
        round_obj.save()
        return round_obj
    
    @transaction.atomic
    def end_round(self, round_obj: GameRound) -> GameRound:
        """Mark a round as ended."""
        round_obj.ended_at = timezone.now()
        round_obj.save()
        return round_obj
    
    def calculate_score(self, is_correct: bool, response_time: float, max_time: int = 30) -> int:
        """Calculate base points for an answer (Option C — Linear + Rank).
        
        Correct answer: 100 - (response_time * 3), minimum 10 points.
        Wrong answer: 0 points.
        Rank bonus is added separately in submit_answer().
        """
        if not is_correct:
            return 0
        base_points = max(10, 100 - int(response_time * 3))
        return base_points
    
    @transaction.atomic
    def submit_answer(self, player: GamePlayer, round_obj: GameRound, answer: str, response_time: float) -> GameAnswer:
        """Submit and score a player's answer."""
        is_correct = answer == round_obj.correct_answer
        points = self.calculate_score(is_correct, response_time, round_obj.duration)
        
        # Rank bonus: +10 for 1st correct, +5 for 2nd, +2 for 3rd
        rank_bonus = 0
        if is_correct:
            correct_before = GameAnswer.objects.filter(
                round=round_obj, is_correct=True
            ).count()
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
            response_time=response_time
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
            
            # Update user statistics
            user = player.user
            user.total_games_played += 1
            user.total_points += player.score
            if rank == 1:
                user.total_wins += 1
            user.save()
            
            # Check for perfect game (all answers correct)
            correct_answers = GameAnswer.objects.filter(
                player=player,
                round__game=game,
                is_correct=True,
            ).count()
            perfect_game = total_rounds > 0 and correct_answers == total_rounds
            
            # Check and award achievements
            round_data = {'perfect_game': perfect_game}
            achievement_service.check_and_award(user, game=game, round_data=round_data)
        
        return game


# Singleton instances
question_generator_service = QuestionGeneratorService()
game_service = GameService()
