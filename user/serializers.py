import datetime
from typing import Dict, Any

import rest_framework_simplejwt.authentication
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from plan.models import Subscription
from user.models import *
from hashlib import sha256
from datetime import timedelta
from django.utils import timezone


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False,
            is_staff=False,
            is_superuser=False
        )

        user.set_password(validated_data['password'])
        expire_date = timezone.now() + timedelta(hours=3)
        user_token = UserToken(
            user=user,
            token=sha256(f"{user.username}{timezone.now().timestamp()}".encode('utf-8')).hexdigest(),
            expire_date=expire_date
        )

        with transaction.atomic():
            user.save()
            user_token.save()

        return user, user_token


class LoginUserSerializers(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data['email'] = self.user.email
        data['username'] = self.user.username
        data['is_premium'] = False
        data['days'] = None
        now = timezone.now()
        premium = Subscription.objects.filter(user=self.user).order_by('-end_date').first()
        if premium is not None:
            if premium.end_date > now:
                data['is_premium'] = True
                c = premium.end_date - now
                data['days'] = c.days

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class LoginSuperUserSerializers(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)

        if not self.user.is_superuser:
            raise exceptions.AuthenticationFailed()
        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class DashboardUserSerializer(serializers.ModelSerializer):
    seen_movies = serializers.IntegerField()
    is_premium = serializers.BooleanField()
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'date_joined', 'is_premium', 'seen_movies', 'full_name')

    @staticmethod
    def get_full_name(obj):
        return '{} {}'.format(obj.first_name, obj.last_name)


class CommentUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'username')

    @staticmethod
    def get_full_name(obj):
        return '{} {}'.format(obj.first_name, obj.last_name)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh"] = str(refresh)

        user = User.objects.get(id=refresh['user_id'])
        data['email'] = user.email
        data['is_premium'] = False
        data['days'] = None
        data['email'] = user.email
        data['username'] = user.username

        now = timezone.now()
        premium = Subscription.objects.filter(user=user).order_by('-end_date').first()
        if premium is not None:
            if premium.end_date > now:
                data['is_premium'] = True
                c = premium.end_date - now
                data['days'] = c.days

        return data
