"""
Services for game logic.
"""
import random
import logging
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from .models import Game, GamePlayer, GameRound, GameAnswer, GameStatus
from apps.playlists.services import spotify_service, SpotifyAPIError
from apps.playlists.hybrid_service import hybrid_spotify_service

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """Service to generate quiz questions from Spotify tracks."""
    
    QUESTION_TYPES = ['guess_title', 'guess_artist']
    
    def __init__(self):
        self.spotify = spotify_service
        self.hybrid_spotify = hybrid_spotify_service
    
    def generate_questions(
        self,
        playlist_id: str,
        num_questions: int = 10,
        question_type: str = 'guess_title',
        user=None
    ) -> List[Dict]:
        """
        Generate quiz questions from a Spotify playlist.
        
        Uses OAuth if user has connected Spotify, otherwise Client Credentials.
        
        Args:
            playlist_id: Spotify playlist ID
            num_questions: Number of questions to generate
            question_type: Type of question ('guess_title' or 'guess_artist')
            user: Django user (optional, for OAuth)
        
        Returns:
            List of question dictionaries
        """
        # Get tracks from playlist using hybrid service
        try:
            tracks = self.hybrid_spotify.get_playlist_tracks(
                playlist_id, 
                limit=50,
                user=user
            )
        except SpotifyAPIError as e:
            error_msg = str(e)
            logger.error(f"Failed to get tracks from playlist {playlist_id}: {error_msg}")
            
            if "403" in error_msg or "Forbidden" in error_msg:
                raise ValueError(
                    f"Accès refusé à cette playlist Spotify. "
                    f"Les playlists privées ou protégées ne sont pas accessibles avec l'authentification actuelle. "
                    f"Veuillez sélectionner une playlist publique différente."
                )
            elif "404" in error_msg:
                raise ValueError(f"Playlist {playlist_id} introuvable sur Spotify.")
            else:
                raise ValueError(f"Erreur lors de l'accès à la playlist: {error_msg}")
        
        if not tracks or len(tracks) < 4:
            logger.warning(f"Playlist {playlist_id} returned {len(tracks) if tracks else 0} tracks")
            raise ValueError(
                f"La playlist ne contient pas assez de morceaux accessibles ({len(tracks) if tracks else 0} trouvés, minimum 4 requis). "
                f"Certaines playlists peuvent avoir des restrictions d'accès."
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
        
        # Get other track titles as wrong answers
        other_tracks = [t for t in all_tracks if t['spotify_id'] != correct_track['spotify_id']]
        random.shuffle(other_tracks)
        
        wrong_answers = []
        for track in other_tracks:
            if track['name'] != correct_answer and track['name'] not in wrong_answers:
                wrong_answers.append(track['name'])
            if len(wrong_answers) >= 3:
                break
        
        # Need at least 3 wrong answers
        if len(wrong_answers) < 3:
            return None
        
        # Combine and shuffle options
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        
        return {
            'track_id': correct_track['spotify_id'],
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
        
        # Get other artists as wrong answers
        other_tracks = [t for t in all_tracks if t['spotify_id'] != correct_track['spotify_id']]
        random.shuffle(other_tracks)
        
        wrong_answers = []
        for track in other_tracks:
            artist = ', '.join(track['artists'])
            if artist != correct_answer and artist not in wrong_answers:
                wrong_answers.append(artist)
            if len(wrong_answers) >= 3:
                break
        
        # Need at least 3 wrong answers
        if len(wrong_answers) < 3:
            return None
        
        # Combine and shuffle options
        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)
        
        return {
            'track_id': correct_track['spotify_id'],
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
        """
        Start a game and generate rounds.
        
        Uses OAuth for playlist access if host has connected Spotify.
        
        Args:
            game: Game instance to start
        
        Returns:
            Tuple of (updated game, list of rounds)
        """
        if game.status != GameStatus.WAITING:
            raise ValueError("Game is not in waiting status")
        
        if not game.playlist_id:
            raise ValueError("Game must have a playlist")
        
        # Generate questions (using host's Spotify connection if available)
        num_rounds = 10  # Default number of rounds
        questions = self.question_generator.generate_questions(
            game.playlist_id,
            num_questions=num_rounds,
            user=game.host  # Pass host user for OAuth
        )
        
        if not questions:
            raise ValueError("Failed to generate questions from playlist")
        
        # Create rounds
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
                duration=30,  # 30 seconds per round
            )
            rounds.append(round_obj)
        
        # Update game status
        game.status = GameStatus.IN_PROGRESS
        game.started_at = timezone.now()
        game.save()
        
        return game, rounds
    
    def get_current_round(self, game: Game) -> Optional[GameRound]:
        """Get the current active round for a game."""
        return game.rounds.filter(ended_at__isnull=True).order_by('round_number').first()
    
    def get_next_round(self, game: Game) -> Optional[GameRound]:
        """Get the next round to play."""
        current_round = self.get_current_round(game)
        
        if current_round:
            # Current round not finished yet
            return None
        
        # Find first unplayed round
        played_rounds = game.rounds.filter(ended_at__isnull=False).values_list('round_number', flat=True)
        next_round = game.rounds.exclude(round_number__in=played_rounds).order_by('round_number').first()
        
        return next_round
    
    @transaction.atomic
    def end_round(self, round_obj: GameRound) -> GameRound:
        """Mark a round as ended."""
        round_obj.ended_at = timezone.now()
        round_obj.save()
        return round_obj
    
    def calculate_score(
        self,
        is_correct: bool,
        response_time: float,
        max_time: int = 30
    ) -> int:
        """
        Calculate points for an answer.
        
        Args:
            is_correct: Whether the answer is correct
            response_time: Time taken to answer (seconds)
            max_time: Maximum time allowed (seconds)
        
        Returns:
            Points earned
        """
        if not is_correct:
            return 0
        
        # Base points for correct answer
        base_points = 1000
        
        # Time bonus (faster = more points)
        time_bonus = int((1 - (response_time / max_time)) * 500)
        time_bonus = max(0, time_bonus)
        
        return base_points + time_bonus
    
    @transaction.atomic
    def submit_answer(
        self,
        player: GamePlayer,
        round_obj: GameRound,
        answer: str,
        response_time: float
    ) -> GameAnswer:
        """
        Submit and score a player's answer.
        
        Args:
            player: GamePlayer instance
            round_obj: GameRound instance
            answer: Player's answer
            response_time: Time taken to answer
        
        Returns:
            GameAnswer instance
        """
        # Check if answer is correct
        is_correct = answer == round_obj.correct_answer
        
        # Calculate points
        points = self.calculate_score(is_correct, response_time, round_obj.duration)
        
        # Create answer record
        game_answer = GameAnswer.objects.create(
            round=round_obj,
            player=player,
            answer=answer,
            is_correct=is_correct,
            points_earned=points,
            response_time=response_time
        )
        
        # Update player's total score
        player.score += points
        player.save()
        
        return game_answer
    
    @transaction.atomic
    def finish_game(self, game: Game) -> Game:
        """
        Finish a game and calculate final rankings.
        
        Args:
            game: Game instance to finish
        
        Returns:
            Updated game instance
        """
        # Update game status
        game.status = GameStatus.FINISHED
        game.finished_at = timezone.now()
        game.save()
        
        # Calculate rankings
        players = game.players.order_by('-score')
        for rank, player in enumerate(players, start=1):
            player.rank = rank
            player.save()
        
        return game


# Singleton instances
question_generator_service = QuestionGeneratorService()
game_service = GameService()
