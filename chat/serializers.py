from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Message, User, Groups, GroupMessage
from rest_framework.serializers import ModelSerializer, CharField


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = ["pk", "user", "recipient", "timestamp", "body", "avatar", "picture"]

    user = CharField(source="user.username", read_only=True)
    recipient = CharField(source="recipient.username")
    avatar = CharField(source="user.avatar", read_only=True)

    def create(self, validated_data):
        user = self.context["request"].user
        recipient = get_object_or_404(User, username=validated_data["recipient"]["username"])
        msg = Message.objects.create(recipient=recipient, body=validated_data["body"], user=user)
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
