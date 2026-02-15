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
            elif message_type == 'next_round':
                await self.next_round(data)
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
        """Handle player joining the game."""
        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_player_join',
                'player': data.get('player')
            }
        )
    
    async def player_answer(self, data):
        """Handle player submitting an answer."""
        # TODO: Validate answer and calculate score
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_player_answer',
                'player': data.get('player'),
                'answer': data.get('answer')
            }
        )
    
    async def start_game(self, data):
        """Handle game start."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_game_start'
            }
        )
    
    async def next_round(self, data):
        """Handle next round."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_next_round',
                'round_data': data.get('round_data')
            }
        )
    
    # Broadcast handlers
    async def broadcast_player_join(self, event):
        """Send player join notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player': event['player']
        }))
    
    async def broadcast_player_answer(self, event):
        """Send player answer to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'player_answered',
            'player': event['player'],
            'answer': event['answer']
        }))
    
    async def broadcast_game_start(self, event):
        """Send game start to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'game_started'
        }))
    
    async def broadcast_next_round(self, event):
        """Send next round data to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'round_started',
            'round_data': event['round_data']
        }))
