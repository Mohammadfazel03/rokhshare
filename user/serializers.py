from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework import validators
from rest_framework.validators import UniqueValidator
from django.db import transaction
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
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
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
