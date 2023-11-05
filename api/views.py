from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet
from django.core.mail import EmailMessage
from api.permissions import IsSuperUser
from movie.models import Genre, Artist, Country
from movie.serializers import GenreSerializer, CountrySerializer, ArtistSerializer
from user.serializers import RegisterUserSerializer, LoginUserSerializers, LoginSuperUserSerializers
from django.template.loader import render_to_string


# Create your views here.
class AuthViewSet(ViewSet):

    @action(methods=['POST'], detail=False, permission_classes=[AllowAny])
    def register(self, request):
        user_serializer = RegisterUserSerializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            user, user_token = user_serializer.save()
            current_site = get_current_site(request)
            user.get_full_name()
            message = render_to_string('active_email.html', {
                'user': user, 'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user_token.token,
            })
            mail_subject = 'Activate your account.'
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()

        return Response("created", status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginUserSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, permission_classes=[AllowAny], url_path='login/admin')
    def login_admin(self, request):
        serializer = LoginSuperUserSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class GenreViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CountryViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = CountrySerializer
    queryset = Country.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ArtistViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = ArtistSerializer
    queryset = Artist.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
