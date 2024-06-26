from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import login
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.http import HttpRequest, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.utils import phone_validator, get_client_ip
from .models import User, Message, GroupMessage, Phone, LoginVisit, Groups, PrivateMessage
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication
from ChatCompany import settings
from chat.serializers import MessageSerializer, UserSerializer, GroupsSerializer, GroupMessageSerializer, TestSerializer
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
            self.queryset = self.queryset.filter(Private_message=target)
        return super(MessageViewSet, self).list(request, *args, **kwargs)


class PrivateMessageViewSet(ModelViewSet):
    queryset = PrivateMessage.objects.all()
    serializer_class = TestSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        user: User = get_object_or_404(User, pk=request.user.id)
        self.queryset = self.queryset.filter(users__id=user.id)
        return super(PrivateMessageViewSet, self).list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(PrivateMessageViewSet, self).get_serializer_context()
        context["username"] = self.request.user.username
        return context


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
        return Response("Created successfully", status.HTTP_201_CREATED, )


class SetAuthTokenAPI(APIView):

    def post(self, request: HttpRequest):
        """
        sending auth token function:
        checking phone number length is 11 and must be number,
        number must exist in DB,
        generating auth token and expiration time of token

        """
        phone_no = str(request.POST.get("phone_no"))
        if len(phone_no) != 11:
            return JsonResponse({
                "status": "length_issue"
            })
        if not phone_no.isdigit():
            return JsonResponse({
                "status": "not_number"
            })
        try:
            phone = Phone.objects.get(phone_no=phone_no)
        except Phone.DoesNotExist:
            return JsonResponse({
                "status": "not_found"
            })
        phone.set_tk()
        phone.set_expiration_time()
        phone.save()
        # todo: send_api_sms
        return JsonResponse({
            "status": "success",
            "token": phone.token
        })


class AuthTokenCheckAPI(APIView):

    def post(self, request: HttpRequest):
        """
        checking auth_token function:
        checking phone number length is 11 and must be number
        checking token expiration time
        checking same token as DB
        and submit ind DB that user tried to log
        and set token and expiration time to null or blank,
        and finally we log the user
        """
        token = request.POST.get("token")
        phone_no = str(request.POST.get("phone_no"))

        try:
            try:
                phone_validator(phone_no)
            except ValidationError as e:
                return JsonResponse({
                    "status": e.message
                })
            phone: Phone = Phone.objects.get(phone_no=phone_no)
        except Phone.DoesNotExist:
            return JsonResponse({
                "status": "phone_not_found"
            })
        try:
            user = User.objects.get(pk=phone.user.id)
            user_ip = get_client_ip(request)
            LoginVisit.objects.create(ip=user_ip, user_id=user.id)
            minute_ago = timezone.now() - timedelta(minutes=1)
            login_check: LoginVisit = LoginVisit.objects.filter(ip=user_ip, user_id=user.id, timestamp__gt=minute_ago)
            if login_check.count() > 3:
                return JsonResponse({
                    "status": "login_ban"
                })
        except User.DoesNotExist:
            return JsonResponse({
                "status": "user_not_found"
            })
        if timezone.now() > phone.expiration_time:
            return JsonResponse({
                "status": "times_up"
            })
        if token != phone.token:
            return JsonResponse({
                "status": "wrong_token"
            })

        phone.token = ""
        phone.expiration_time = None
        phone.save()
        login(request, user)
        return JsonResponse({
            "status": "success"
        })


class MakeGroupAPI(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest):
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        description = request.POST.get('description')
        users = list(request.POST['users'])
        group = Groups.objects.create(avatar=avatar, title=title, description=description)
        for user in users:
            user = User.objects.get(username=user)
            group.users.add(user)
        notification = {
            "type": "send_message",
            "message": {
                "state": "newGroup",
                "group_id": group.id,
                "title": group.title,
                "avatar": str(group.avatar),
            }
        }

        channel_layer = get_channel_layer()
        users = group.users.all().exclude(id=request.user.id)
        for user in users:
            async_to_sync(channel_layer.group_send)(str(user.id), notification)




class MessageSeenAPI(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest):
        pv_chat = request.POST.get('pvChat', None)
        if pv_chat is not None:
            messages = Message.objects.filter(Private_message_id=pv_chat)
            for message in messages:
                message.is_seen = True
            messages.save()
            Response("success", status=201)
        raise Http404
