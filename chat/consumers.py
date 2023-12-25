# chat/consumers.py
from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
import json


# Private chat Only
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user_id = self.scope["session"]["_auth_user_id"]
        self.group_name = str(user_id)
        print(self.group_name)
        # Join room group
        # print(self.group_name)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # Send message to room group
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'send_message',
                'message': message
            }
        )

    async def send_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({
                'message': message
            }))
# docker run --rm -p 6379:6379 redis:7
