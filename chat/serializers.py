from django.shortcuts import get_object_or_404
from .models import Message, User, Groups, GroupMessage
from rest_framework.serializers import ModelSerializer, CharField


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = ["pk", "user", "recipient", "timestamp", "body"]

    user = CharField(source="user.username", read_only=True)
    recipient = CharField(source="recipient.username")

    def create(self, validated_data):
        user = self.context["request"].user
        recipient = get_object_or_404(User, username=validated_data["recipient"]["username"])
        msg = Message.objects.create(recipient=recipient, body=validated_data["body"], user=user)
        return msg


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]
        # todo: we must get the all fields so users can see their profiles


class GroupsSerializer(ModelSerializer):
    users = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Groups
        fields = "__all__"


class GroupMessageSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMessage
        fields = "__all__"

