from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from django.core.mail import EmailMessage
from api.permissions import IsSuperUser, IsOwner
from movie.models import Genre, Artist, Country, Movie, TvSeries, Season, Episode, MediaGallery, Slider, Collection, \
    Media, Comment, Rating
from movie.serializers import GenreSerializer, CountrySerializer, ArtistSerializer, CreateMovieSerializer, \
    MovieSerializer, CreateSerialSerializer, SerialSerializer, SeasonSerializer, EpisodeSerializer, \
    MediaGallerySerializer, SliderSerializer, CollectionSerializer, MediaInputSerializer, CommentSerializer, \
    RatingSerializer
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


class MovieViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    lookup_field = "media__id"

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateMovieSerializer
        elif self.action in ['retrieve', 'list', 'destroy']:
            return MovieSerializer

    def get_queryset(self):
        if self.action in ['retrieve', 'list', 'destroy', 'partial_update']:
            return Movie.objects.all().select_related("media")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance = instance.media
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({"message": "ok"})


class SeriesViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    lookup_field = "media__id"

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateSerialSerializer
        elif self.action in ['retrieve', 'list', 'destroy']:
            return SerialSerializer

    def get_queryset(self):
        if self.action in ['retrieve', 'list', 'destroy', 'partial_update']:
            return TvSeries.objects.all().select_related("media")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance = instance.media
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response({"message": "ok"})


class SeasonViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = SeasonSerializer
    queryset = Season.objects.all()

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


class EpisodeViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = EpisodeSerializer
    queryset = Episode.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response({"message": "ok"}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class MediaGalleryViewSet(ModelViewSet):
    serializer_class = MediaGallerySerializer
    queryset = MediaGallery.objects.all()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [AllowAny()]
        return [IsSuperUser()]

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class SliderViewSet(ModelViewSet):
    serializer_class = SliderSerializer
    queryset = Slider.objects.all()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [AllowAny()]
        return [IsSuperUser()]

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


class CollectionViewSet(ModelViewSet):
    serializer_class = CollectionSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        elif self.action == 'confirm_collection':
            return [IsSuperUser()]
        elif self.action == 'me_collection':
            return [IsAuthenticated()]
        return [IsOwner()]

    def get_queryset(self):
        if self.action == 'list':
            return Collection.objects.filter(is_confirm=True, is_private=False)
        return Collection.objects.all()

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        request.data['user'] = request.user.id
        request.data['is_confirm'] = request.user.is_superuser
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data._mutable = True
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        request.data['user'] = request.user.id
        request.data['is_confirm'] = request.user.is_superuser or instance.is_confirm
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(methods=['POST'], detail=True, url_path='confirm', url_name='confirm')
    def confirm_collection(self, request, pk):
        confirm = request.data.get('is_confirm', None)
        if confirm is None:
            raise ValidationError("confirm value is wrong")

        if confirm in ['true', 'True', 1]:
            confirm = True
        elif confirm in ['false', False, 0]:
            confirm = False
        else:
            raise ValidationError("expected bool but got string")

        collection = self.get_object()

        collection.is_confirm = confirm
        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_name='my_collection', url_path='me')
    def me_collection(self, request):
        queryset = Collection.objects.filter(user=request.user)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='add', url_name='add')
    def add_media(self, request, pk):
        collection: Collection = self.get_object()
        media_serializer = MediaInputSerializer(data=request.data)
        media_serializer.is_valid(raise_exception=True)
        for media in media_serializer.data['media']:
            collection.media.add(Media.objects.get(pk=media))

        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='remove', url_name='remove')
    def remove_media(self, request, pk):
        collection: Collection = self.get_object()
        media_serializer = MediaInputSerializer(data=request.data)
        media_serializer.is_valid(raise_exception=True)
        for media in media_serializer.data['media']:
            collection.media.remove(Media.objects.get(pk=media))

        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsSuperUser()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        elif self.action == 'confirm_comment':
            return [IsSuperUser()]
        elif self.action == 'me_comment':
            return [IsAuthenticated()]
        return [IsOwner()]

    def get_queryset(self):
        return Comment.objects.all()

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        request.data['user'] = request.user.id
        request.data['is_confirm'] = request.user.is_superuser
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data._mutable = True
        instance = self.get_object()
        request.data['user'] = request.user.id
        request.data['is_confirm'] = request.user.is_superuser or instance.is_confirm
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(methods=['POST'], detail=True, url_path='confirm', url_name='confirm')
    def confirm_comment(self, request, pk):
        confirm = request.data.get('is_confirm', None)
        if confirm is None:
            raise ValidationError("confirm value is wrong")

        if confirm in ['true', 'True', 1]:
            confirm = True
        elif confirm in ['false', False, 0]:
            confirm = False
        else:
            raise ValidationError("expected bool but got string")

        collection = self.get_object()

        collection.is_confirm = confirm
        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_name='my_comment', url_path='me')
    def me_comment(self, request):
        queryset = Comment.objects.filter(user=request.user).order_by('created_at')
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RatingViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    serializer_class = RatingSerializer
    queryset = Rating.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_name='my_rating', url_path='me')
    def me_rating(self, request):
        queryset = Rating.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
