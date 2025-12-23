import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import ChatRoom, Message, UserProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user online status
        if not isinstance(self.user, AnonymousUser):
            await self.update_user_status(True)
            
            # Send join notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat(),
                }
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user online status
        if not isinstance(self.user, AnonymousUser):
            await self.update_user_status(False)
            
            # Send leave notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat(),
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            content = text_data_json['content']
            parent_id = text_data_json.get('parent_id')
            
            # Save message to database
            message = await self.save_message(content, parent_id)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message.id),
                    'sender_id': str(self.user.id),
                    'sender_username': self.user.username,
                    'content': content,
                    'timestamp': message.timestamp.isoformat(),
                    'parent_id': parent_id,
                }
            )
        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'is_typing': text_data_json['is_typing'],
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            'parent_id': event.get('parent_id'),
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def save_message(self, content, parent_id=None):
        room = ChatRoom.objects.get(id=self.room_id)
        parent = None
        
        if parent_id:
            try:
                parent = Message.objects.get(id=parent_id)
            except Message.DoesNotExist:
                pass
        
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            parent_message=parent
        )
        return message

    @database_sync_to_async
    def update_user_status(self, status):
        try:
            profile = UserProfile.objects.get(user=self.user)
            profile.update_online_status(status)
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            UserProfile.objects.create(
                user=self.user,
                online_status=status,
                last_seen=timezone.now()
            )