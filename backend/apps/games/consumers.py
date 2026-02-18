"""
WebSocket consumers for games.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for game rooms."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to game room'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route message to appropriate handler
            if message_type == 'player_join':
                await self.player_join(data)
            elif message_type == 'player_answer':
                await self.player_answer(data)
            elif message_type == 'start_game':
                await self.start_game(data)
            elif message_type == 'start_round':
                await self.start_round(data)
            elif message_type == 'end_round':
                await self.end_round(data)
            elif message_type == 'next_round':
                await self.next_round(data)
            elif message_type == 'finish_game':
                await self.finish_game(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def player_join(self, data):
        """Handle player joining the game (legacy WS message - prefer API call)."""
        # Get updated game data
        game_data = await self.get_game_data()
        
        # Broadcast to room group with updated player list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_player_join',
                'player': data.get('player'),
                'game_data': game_data
            }
        )
    
    @database_sync_to_async
    def get_game_data(self):
        """Get game data with players."""
        from .models import Game
        from .serializers import GameSerializer, GamePlayerSerializer
        from django.conf import settings
        
        try:
            game = Game.objects.get(room_code=self.room_code)
            
            # Build game data manually to include proper avatar URLs
            players_data = []
            for player in game.players.select_related('user').all():
                avatar_url = None
                if player.user.avatar:
                    # Build absolute URL for avatar
                    avatar_url = f"http://localhost:8000{player.user.avatar.url}"
                
                players_data.append({
                    'id': player.id,
                    'user': player.user.id,
                    'username': player.user.username,
                    'avatar': avatar_url,
                    'score': player.score,
                    'rank': player.rank,
                    'is_connected': player.is_connected,
                    'joined_at': player.joined_at.isoformat()
                })
            
            game_data = {
                'id': str(game.id),
                'room_code': game.room_code,
                'host': game.host.id,
                'host_username': game.host.username,
                'mode': game.mode,
                'status': game.status,
                'max_players': game.max_players,
                'playlist_id': game.playlist_id,
                'is_online': game.is_online,
                'answer_mode': game.answer_mode,
                'round_duration': game.round_duration,
                'time_between_rounds': game.time_between_rounds,
                'players': players_data,
                'player_count': len(players_data),
                'created_at': game.created_at.isoformat(),
                'started_at': game.started_at.isoformat() if game.started_at else None,
                'finished_at': game.finished_at.isoformat() if game.finished_at else None,
            }
            
            return game_data
        except Game.DoesNotExist:
            return None
    
    async def player_answer(self, data):
        """Handle player submitting an answer."""
        player_username = data.get('player')
        answer = data.get('answer')
        response_time = data.get('response_time', 0)
        
        # Broadcast that player answered (without revealing correctness yet)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_player_answer',
                'player': player_username,
                'answered': True
            }
        )
    
    async def start_game(self, data):
        """Handle game start."""
        # Get initial game data
        game_data = await self.get_game_data()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_game_start',
                'game_data': game_data
            }
        )
    
    async def start_round(self, data):
        """Handle round start."""
        round_data = data.get('round_data')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_round_start',
                'round_data': round_data
            }
        )
    
    async def end_round(self, data):
        """Handle round end."""
        round_results = data.get('results')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_round_end',
                'results': round_results
            }
        )
    
    async def next_round(self, data):
        """Handle next round."""
        round_data = data.get('round_data')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_next_round',
                'round_data': round_data
            }
        )
    
    async def finish_game(self, data):
        """Handle game finish."""
        results = data.get('results')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_game_finish',
                'results': results
            }
        )
    
    # Broadcast handlers
    async def broadcast_player_join(self, event):
        """Send player join notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player': event['player'],
            'game_data': event.get('game_data')
        }))
    
    async def broadcast_player_answer(self, event):
        """Send player answer notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'player_answered',
            'player': event['player'],
            'answered': event.get('answered', True)
        }))
    
    async def broadcast_game_start(self, event):
        """Send game start to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'game_data': event.get('game_data')
        }))
    
    async def broadcast_round_start(self, event):
        """Send round start to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'round_started',
            'round_data': event['round_data']
        }))
    
    async def broadcast_round_end(self, event):
        """Send round end with results to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'round_ended',
            'results': event['results']
        }))
    
    async def broadcast_next_round(self, event):
        """Send next round data to WebSocket."""
        message = {
            'type': 'next_round',
            'round_data': event['round_data'],
        }
        if 'updated_players' in event:
            message['updated_players'] = event['updated_players']
        await self.send(text_data=json.dumps(message))
    
    async def broadcast_game_finish(self, event):
        """Send game finish with final results to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'results': event['results']
        }))
