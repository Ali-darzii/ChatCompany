from datetime import timedelta

from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from .models import Company, User, Phone, LoginVisit
from django.utils import timezone
from django.contrib.auth import login, logout
from utils.utils import get_client_ip, phone_validator
from django.views.generic import TemplateView, View
from django.urls import reverse


class SignUpView(View):
    """

    0.company must exist
    1.username validation(in model save function)
    2.phone validation(in model save function )
    3.max size check for DB

    """

    def get(self, request):
        return render(request, 'chat/sign-up.html')

    def post(self, request):
        username: str = request.POST['username']
        name: str = request.POST['name']
        phone_no = request.POST['phone_no']
        role = request.POST['role']
        company = request.POST['company']
        try:
            company = Company.objects.get(title__iexact=company)
        except Company.DoesNotExist:
            return JsonResponse({
                "status": "company_not_found"
            })
        try:
            user = User.objects.create(name=name, username=username, role=role, company=company)
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


def set_auth_token(request: HttpRequest):
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


def auth_token_check(request: HttpRequest):
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
        login_check: LoginVisit = LoginVisit.objects.filter(ip=user_ip, user_id=user.id,timestamp__gt=minute_ago)
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


def logout_view(request: HttpRequest):
    logout(request)
    return redirect(reverse('login_page'))
