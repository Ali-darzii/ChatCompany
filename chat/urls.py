from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

from .api import UserViewSet, MessageViewSet, GroupsApiView, GroupMessagesApiView

router = DefaultRouter()

router.register(r'message', MessageViewSet, basename='message-api')
router.register(r'user', UserViewSet, basename='user-api')

urlpatterns = [
    path(r'api/v1/', include(router.urls)),
    path("api/v1/groups/", GroupsApiView.as_view(), name='groups_api'),
    path("api/v1/Group-message/", GroupMessagesApiView.as_view(), name='group_messages_api'),

    path("login/", views.Login.as_view(), name="login_page"),
    path("sign-up/", views.SignUpView.as_view(), name="sign_up_page"),
    path("", views.Room.as_view(), name="home_page"),
    path("logout/", views.logout_view, name="logout"),
    path("send-token/", views.set_auth_token),
    path("check-token/", views.auth_token_check),
]
