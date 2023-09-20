import re

from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from chatapp.models import Message, User


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Username Already Taken!",
                lookup="iexact",
            )
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Email Already Exist!",
                lookup="iexact",
            )
        ]
    )
    password = serializers.CharField()

    class Meta:
        fields = ("username", "email", "password")

    def validate_username(self, value):
        if not re.fullmatch(settings.USERNAME_REGEX, value):
            raise serializers.ValidationError(
                "Username should contain alphanumerics, hyphens, underscores, or periods"
            )
        return value

    def create(self, validated_data):
        validated_data["username"] = validated_data["username"].lower()
        validated_data["email"] = validated_data["email"].lower()
        validated_data["password"] = make_password(validated_data["password"])
        user = User.objects.create(**validated_data)
        return user


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username")
    receiver = serializers.CharField(source="receiver.username")

    class Meta:
        model = Message
        fields = ["sender", "receiver", "content", "timestamp"]
