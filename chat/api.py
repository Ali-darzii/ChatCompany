from django.db.models import Q
from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, Message, GroupMessage
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication
from ChatCompany import settings
from chat.serializers import MessageSerializer, UserSerializer, GroupsSerializer, GroupMessageSerializer
from rest_framework import status


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication scheme used by DRF. DRF's SessionAuthentication uses
    Django's session framework for authentication which requires CSRF to be
    checked. In this case we are going to disable CSRF tokens for the API.
    """

    def enforce_csrf(self, request):
        return


class MessagePagination(PageNumberPagination):
    """

    Limit message prefetch to one page.

    """
    page_size = settings.MESSAGES_TO_LOAD


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    allowed_methods = ["GET", "POST", "HEAD", "OPTIONS"]
    pagination_class = MessagePagination

    def list(self, request, *args, **kwargs):
        target = self.request.query_params.get("target", None)
        if target is not None:
            self.queryset = self.queryset.filter(
                Q(user=request.user, recipient__username=target) | Q(user__username=target, recipient=request.user))

        return super(MessageViewSet, self).list(request, *args, **kwargs)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        user: User = get_object_or_404(User, pk=request.user.id)
        self.queryset = self.queryset.filter(company_id=user.company_id)
        self.queryset = self.queryset.exclude(pk=user.id).distinct()
        return super(UserViewSet, self).list(request, *args, **kwargs)


class GroupsApiView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest):
        user: User = User.objects.get(pk=request.user.id).group_users.all()
        groups = GroupsSerializer(user, many=True)
        return Response(groups.data, status.HTTP_200_OK)


class GroupMessagesApiView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest):
        target = self.request.query_params.get("target", None)
        if target is not None:
            group_message: GroupMessage = GroupMessage.objects.filter(group_id=target)
            messages = GroupMessageSerializer(group_message, many=True)
            return Response(messages.data, status.HTTP_200_OK)
        raise Http404

    def post(self, request: HttpRequest):
        body = request.POST.get("body", None)
        group_id = request.POST.get("group", None)
        GroupMessage.objects.create(body=body, group_id=group_id, user_id=self.request.user.id)
        # messages = GroupMessageSerializer(group_message, many=True)
        return Response("Created successfully", status.HTTP_201_CREATED)
