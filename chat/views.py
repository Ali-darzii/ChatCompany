from datetime import timedelta

from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from rest_framework.views import APIView

from .models import User, Phone, LoginVisit
from django.utils import timezone
from django.contrib.auth import login, logout
from utils.utils import get_client_ip, phone_validator
from django.views.generic import TemplateView, View
from django.urls import reverse


class SignUpView(View):
    """

    1.username validation(in model save function)
    2.phone validation(in model save function )
    3.max size check for DB

    """

    def get(self, request):
        user = User.objects.get(pk=1)
        Phone.objects.create(user_id=user.id, phone_no='09191771660', token='')
        return render(request, 'chat/sign-up.html')

    def post(self, request):
        username: str = request.POST['username']
        name: str = request.POST['name']
        phone_no = request.POST['phone_no']
        try:
            user = User.objects.create(name=name, username=username)
        except ValidationError as e:
            return JsonResponse({
                "status": e.message
            })
        try:
            Phone.objects.create(phone_no=phone_no, user=user)
        except ValidationError as e:
            return JsonResponse({
                "status": e.message
            })
        return JsonResponse({
            "status": "success"
        })


class Login(TemplateView):
    template_name = "chat/login.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse("home_page"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        return context


class Room(TemplateView):
    template_name = "chat/room.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(reverse('login_page'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["request"] = self.request
        return context


def logout_view(request: HttpRequest):
    logout(request)
    return redirect(reverse('login_page'))
