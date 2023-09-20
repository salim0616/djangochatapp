from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = "username"
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    token_expiry = models.DateTimeField(null=True)
    is_online = models.BooleanField(default=False)
    REQUIRED_FIELDS = ["email", "password"]

    class Meta:
        db_table = "users"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="msg_sender"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="msg_receiver"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
