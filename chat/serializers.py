from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import serializers
import rest_framework.fields as fields

from .models import Message, User, Groups, GroupMessage, PrivateMessage
from rest_framework.serializers import ModelSerializer, CharField


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = ["pk", "user", "avatar", "timestamp", "body", "picture"]

    user = CharField(source="user.username", read_only=True)
    avatar = CharField(source="user.avatar", read_only=True)

    def create(self, validated_data):
        user = self.context["request"].user
        private_chat = self.context["request"].POST.get("pv_chat")
        msg = Message.objects.create(Private_message_id=private_chat, body=validated_data["body"],
                                     user_id=user.id)
        return msg


class UserSerializer(ModelSerializer):
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ["username", "avatar"]


class GroupsSerializer(ModelSerializer):
    users = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Groups
        exclude = ["admin", "description"]


class GroupMessageSerializer(ModelSerializer):
    avatar = CharField(source="user.avatar", read_only=True)
    user = CharField(source="user.username", read_only=True)

    class Meta:
        model = GroupMessage
        fields = ["body", "user", "group", "timestamp", "avatar", "picture"]


class TestSerializer(ModelSerializer):
    users = UserSerializer(read_only=True, many=True)

    class Meta:
        model = PrivateMessage
        fields = ["id", "timestamp", "users"]

    def to_representation(self, instance):
        # Filter out users with username 'authenticated user'
        username = self.context['username']
        users_data = [
            user_data for user_data in super().to_representation(instance)['users']
            if user_data['username'] != username
        ]

        return {
            "id": instance.id,
            "timestamp": instance.timestamp,
            "users": users_data
        }
