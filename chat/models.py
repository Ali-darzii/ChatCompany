from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin
from django.http import Http404
from django.utils import timezone
from utils.utils import username_validator, phone_validator
from django.db.models import SET_NULL
import random
from datetime import datetime, timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError


class Company(models.Model):
    title = models.CharField(max_length=200, unique=True)
    url = models.SlugField(unique=True)
    city = models.CharField(max_length=80)

    def __str__(self):
        return str(self.title)

    class Meta:
        db_table = "Company_DB"
        verbose_name = "company"
        verbose_name_plural = "companies"


class User(AbstractUser):
    """
    * for authentication user must have(statements):
    (1.name, 2.company, 3.phone_no (from PhoneMessage_DB), 4.role)
    
    which must be written manually in DB(so actually there is no signup form for users)
    because the policy of this site is the company that Purchased subscription of this 
    site must give the statements!

    """

    first_name = None
    last_name = None
    email = None
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=90, blank=True, null=True, unique=True, validators=[
        username_validator
    ])
    avatar = models.ImageField(upload_to="images/user_avatar", blank=True, null=True)
    role = models.CharField(max_length=200)
    description = models.TextField(max_length=70, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="User_in_company")

    REQUIRED_FIELDS = ["name", "role", "company"]

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.id is None:
            username_validator(self.username)
            if User.objects.filter(username=self.username).exists():
                raise ValidationError('username_taken')

            if not 3 <= len(self.name) <= 100 or self.name is None:
                raise ValidationError('name_format')
            if not 3 <= len(self.role) <= 200:
                raise ValidationError('role_format')
            if self.description == '':
                self.description = None
            if self.description is not None and not 1 <= len(self.description) <= 70:
                raise ValidationError('description_format')

        super(User, self).save(*args, **kwargs)


class Groups(models.Model):
    avatar = models.ImageField(upload_to="images/group_avatar", blank=True, null=True)
    title = models.CharField(max_length=25)
    description = models.CharField(max_length=65, null=True, blank=True)
    users = models.ManyToManyField(User, db_index=True, related_name="group_users")
    admin = models.ManyToManyField(User, related_name="group_admin")

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "Groups_DB"


class GroupMessage(models.Model):
    body = models.TextField(db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, db_index=True)
    picture = models.ImageField(upload_to='images/group_message_picture', blank=True, null=True, db_index=True)

    def __str__(self):
        return self.body

    def notify_ws_clients(self):
        """

        Inform client there is new message

        """
        notification = {
            "type": "send_message",
            "message": {
                "state": "groupMessage",
                "group_id": self.group.id,
                "timestamp": str(self.timestamp),
                "body": self.body,
                "user": self.user.username,
                "avatar": str(self.user.avatar.url),
            }
        }

        channel_layer = get_channel_layer()
        users = self.group.users.all()
        for user in users:
            async_to_sync(channel_layer.group_send)(str(user.id), notification)

    def save(self, *args, **kwargs):
        self.body = self.body.strip()
        super(GroupMessage, self).save(*args, **kwargs)
        if self.id is not None:
            self.notify_ws_clients()

    class Meta:
        db_table = "GroupMessage_DB"
        ordering = ('-timestamp',)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="from_user", db_index=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="to_user", db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    body = models.TextField()
    picture = models.ImageField(upload_to="images/message_picture", null=True, blank=True)

    def __str__(self):
        return self.id

    def characters(self):
        """
        function to count body characters.
        :return: body's char number

        """
        return len(self.body)

    def notify_ws_clients(self):
        """
        
        Inform client there is new message

        """
        notification = {
            "type": "send_message",
            "message": {
                "state": "message",
                "body": self.body,
                "timestamp": str(self.timestamp),
                "recipient": self.recipient.username,
                "user": self.user.username,
                "avatar": str(self.user.avatar.url),
            }
        }
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(str(self.user.id), notification)
        async_to_sync(channel_layer.group_send)(str(self.recipient.id), notification)

    def save(self, *args, **kwargs):
        """
        Trims white spaces, saves the message and notifies the recipient via WS
        if the message is new.
        
        """
        new = self.id
        self.body = self.body.strip()
        super(Message, self).save(*args, **kwargs)
        if new is None:
            self.notify_ws_clients()

    class Meta:
        db_table = "Message_DB"
        ordering = ('-timestamp',)


class Phone(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="phone_message",
    )
    token = models.CharField(max_length=6, blank=True)
    expiration_time = models.DateTimeField(blank=True, null=True)
    phone_no = models.CharField(max_length=11, unique=True, validators=[
        phone_validator
    ])

    def __str__(self):
        return f"{self.user} | {self.phone_no}"

    def set_tk(self):
        self.token = random.randrange(1000, 9999)

    def set_expiration_time(self):
        """
        time_ex: time that token get expired
        it's set on one minute
        """
        time_ex = 1

        self.expiration_time = timezone.now() + timedelta(minutes=time_ex)

    #     todo: we deleted self.save but didn't do test
    def save(self, *args, **kwargs):
        if self.id is None:
            phone_validator(self.phone_no)
        super(Phone, self).save(*args, **kwargs)

    class Meta:
        db_table = "Phone_DB"


class LoginVisit(models.Model):
    ip = models.CharField(max_length=30)
    user = models.ForeignKey(User, blank=True, on_delete=models.CASCADE, related_name="index_visit")
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        if str(self.user) != '':
            return f"{self.user.name} | {self.ip}"
        return str(self.ip)

    class Meta:
        db_table = "LoginVisit_DB"
