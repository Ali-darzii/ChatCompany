import re
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.utils.translation import activate
from django.utils import timezone



def phone_validator(phone_no: str):
    """

    phone number character must be 11
    must start with 09
    must only contain numbers

    """
    if phone_no.isdigit() and len(phone_no) == 11 and phone_no.startswith('09'):
        return phone_no

    raise ValidationError('format_issue')


def username_validator(username: str):
    """
    username only contains alphabet , numbers and
    underscores two or more underscores can't be to
    gather the first letter can not be underscores
    and numbers and need to be unique.

    """
    # username_check = User.objects.filter(username=username).exists()
    if 5 <= len(username) <= 90 or username is not None:
        if all(char.isalnum() or char == "_" for char in username):
            if not re.findall("__", username):
                if not all(char.isdigit() or char == "_" for char in username[0]):
                    return username
    raise ValidationError('format_issue')


def get_client_ip(request: HttpRequest):
    """
    if http-x found get it
    if didn't find it get the remote-addr
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for is not None:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
