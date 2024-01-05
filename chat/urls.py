from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

from .api import (PrivateMessageViewSet, MessageViewSet, GroupsApiView, GroupMessagesApiView, SetAuthTokenAPI, AuthTokenCheckAPI,
                  MakeGroupAPI)

router = DefaultRouter()

router.register(r'message', MessageViewSet, basename='message-api')
router.register(r'user', PrivateMessageViewSet, basename='user-api')

urlpatterns = [
    path(r'api/v1/', include(router.urls)),
    path("api/v1/groups/", GroupsApiView.as_view(), name='groups_api'),
    path("api/v1/Group-message/", GroupMessagesApiView.as_view(), name='group_messages_api'),
    path("api/v1/send-token/", SetAuthTokenAPI.as_view(), name="set_auth_token"),
    path("api/v1/check-token/", AuthTokenCheckAPI.as_view(), name="auth_token_check"),

    path("", views.Room.as_view(), name="home_page"),
    path('make-groupe', MakeGroupAPI.as_view(), name='make-group'),
    path("login/", views.Login.as_view(), name="login_page"),
    path("sign-up/", views.SignUpView.as_view(), name="sign_up_page"),
    path("logout/", views.logout_view, name="logout"),
]
