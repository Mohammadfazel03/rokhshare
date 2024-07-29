import hashlib
from datetime import timedelta
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status, mixins, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from django.core.mail import EmailMessage
from advertise.models import AdvertiseSeen, Advertise
from advertise.serializers import DashboardAdvertiseSerializer
from api.permissions import IsSuperUser, IsOwner
from movie.models import Genre, Artist, Country, Movie, TvSeries, Season, Episode, MediaGallery, Slider, Collection, \
    Media, Comment, Rating, SeenMedia, MediaFile
from movie.serializers import GenreSerializer, CountrySerializer, ArtistSerializer, CreateMovieSerializer, \
    MovieSerializer, CreateSerialSerializer, SerialSerializer, SeasonSerializer, EpisodeSerializer, \
    MediaGallerySerializer, SliderSerializer, CollectionSerializer, MediaInputSerializer, CommentSerializer, \
    RatingSerializer, DashboardCommentSerializer, DashboardSliderSerializer, AdminMovieSerializer, \
    AdminTvSeriesSerializer, AdminCollectionSerializer, MediaFileSerializer
from plan.serializers import DashboardPlanSerializer
from user.models import User
from user.serializers import RegisterUserSerializer, LoginUserSerializers, LoginSuperUserSerializers, \
    DashboardUserSerializer
from django.template.loader import render_to_string
from django.db.models import Q, Exists, OuterRef, Case, When, Value, BooleanField
from plan.models import Subscription, Plan
from django.db.models import Count


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
    queryset = Genre.objects.filter().order_by('-pk')

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
    queryset = Country.objects.filter().order_by('-pk')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'id']

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
    queryset = Artist.objects.filter().order_by('-pk')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'id']

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
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateMovieSerializer
        elif self.action in ['retrieve', 'list']:
            return MovieSerializer

    def get_queryset(self):
        if self.action in ['retrieve', 'list', 'partial_update']:
            return Movie.objects.filter().select_related("media").order_by('-pk')
        elif self.action in ['destroy']:
            return Movie.objects.filter()

    def get_object(self):
        if self.action in ['partial_update']:
            return super().get_object().media
        return super().get_object()


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


class DashboardViewSet(GenericViewSet):
    permission_classes = [IsSuperUser]

    @action(methods=['get'], detail=False, url_name='header', url_path='header')
    def header_information(self, request):
        now = timezone.now()
        users = User.objects.aggregate(
            total=Count('id'),
            old=Count('id', filter=Q(date_joined__lte=now - timedelta(days=7))),
        )
        movies = SeenMedia.objects.aggregate(
            total=Count('id'),
            old=Count('id', filter=Q(created_at__lte=now - timedelta(days=7))),
        )

        vip = Subscription.objects.aggregate(
            total=Count('id', filter=Q(end_date__gte=now)),
            old=Count('id',
                      filter=Q(end_date__gte=now - timedelta(days=7)) & Q(created_at__lte=now - timedelta(days=7))),
        )

        ads = AdvertiseSeen.objects.aggregate(
            total=Count('id'),
            old=Count('id', filter=Q(created_at__lte=now - timedelta(days=7)))
        )

        user_ratio = 0
        if users['total'] > 100:
            user_ratio = (users['total'] - users['old']) / users['total'] * 100

        movie_ratio = 0
        if movies['total'] > 100:
            movie_ratio = (movies['total'] - movies['old']) / movies['total'] * 100

        ads_ratio = 0
        if ads['total'] > 100:
            ads_ratio = (ads['total'] - ads['old']) / ads['total'] * 100

        vip_ratio = 0
        if vip['total'] > 100:
            vip_ratio = (vip['total'] - vip['old']) / vip['total'] * 100

        return Response(
            {
                "users": users['total'],
                "user_ratio": user_ratio,
                "movies": movies['total'],
                "movie_ratio": movie_ratio,
                "ads": ads['total'],
                "ads_ratio": ads_ratio,
                "vip": vip['total'],
                "vip_ratio": vip_ratio
            }
        )

    @action(methods=['get'], detail=False, url_name='recently_user', url_path='recently_user')
    def recently_user(self, request):
        now = timezone.now()
        is_premium = Exists(Subscription.objects.filter(user=OuterRef("pk"), end_date__gt=now))
        seen_movies = Count("seenmedia")
        recently_users = User.objects.filter(is_superuser=False).annotate(seen_movies=seen_movies,
                                                                          is_premium=is_premium).order_by(
            "-date_joined").all()[:10]
        recently_users_serializer = DashboardUserSerializer(recently_users, many=True)

        return Response(recently_users_serializer.data)

    @action(methods=['get'], detail=False, url_name='popular_plan', url_path='popular_plan')
    def popular_plan(self, request):
        plan = Plan.objects.annotate(count_of_sub=Count("subscription")).order_by("-count_of_sub").all()[:10]
        plan_serializer = DashboardPlanSerializer(plan, many=True)
        return Response(plan_serializer.data)

    @action(methods=['get'], detail=False, url_name='recently_comment', url_path='recently_comment')
    def recently_comment(self, request):
        comment = Comment.objects.all().order_by("-created_at")[:10]
        comment_serializer = DashboardCommentSerializer(comment, many=True)
        return Response(comment_serializer.data)

    @action(methods=['get'], detail=False, url_name='slider', url_path='slider')
    def slider(self, request):
        slider = Slider.objects.all().order_by("-priority")
        slider_serializer = DashboardSliderSerializer(slider, many=True)
        return Response(slider_serializer.data)

    @action(methods=['get'], detail=False, url_name='advertise', url_path='advertise')
    def advertise(self, request):
        advertise = Advertise.objects.annotate(view_number=Count("advertiseseen")).order_by("-created_at").all()[:10]
        advertise_serializer = DashboardAdvertiseSerializer(advertise, many=True)
        return Response(advertise_serializer.data)


class AdminMediaViewSet(GenericViewSet):
    permission_classes = [IsSuperUser]

    @action(methods=['get'], detail=False, url_name='movie', url_path='movie')
    def movie(self, request, *args, **kwargs):
        movies = Movie.objects.select_related('media').order_by('-pk')
        queryset = self.filter_queryset(movies)
        page = self.paginate_queryset(queryset)
        serializer = AdminMovieSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=False, url_name='series', url_path='series')
    def series(self, request, *args, **kwargs):
        series = TvSeries.objects.annotate(episode_number=Count("season__episode")).select_related('media').order_by(
            '-pk')
        queryset = self.filter_queryset(series)
        page = self.paginate_queryset(queryset)
        serializer = AdminTvSeriesSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=False, url_name='genre', url_path='genre')
    def genre(self, request, *args, **kwargs):
        genres = Genre.objects.filter()
        queryset = self.filter_queryset(genres)
        serializer = GenreSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_name='country', url_path='country')
    def country(self, request, *args, **kwargs):
        countries = Country.objects.filter()
        queryset = self.filter_queryset(countries)
        serializer = CountrySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_name='artist', url_path='artist')
    def artist(self, request, *args, **kwargs):
        artists = Artist.objects.filter().order_by("-pk")
        queryset = self.filter_queryset(artists)
        page = self.paginate_queryset(queryset)
        serializer = ArtistSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=False, url_name='slider', url_path='slider')
    def slider(self, request, *args, **kwargs):
        sliders = Slider.objects.filter().order_by("-pk")
        queryset = self.filter_queryset(sliders)
        page = self.paginate_queryset(queryset)
        serializer = DashboardSliderSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=False, url_name='collection', url_path='collection')
    def collection(self, request, *args, **kwargs):
        collections = Collection.objects.annotate(
            can_edit=Case(
                When(
                    user=request.user, then=Value(True)),
                default=Value(False), output_field=BooleanField()
            )
        ).order_by('-can_edit')
        queryset = self.filter_queryset(collections)
        page = self.paginate_queryset(queryset)
        serializer = AdminCollectionSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class MediaUploaderView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsSuperUser]

    def post(self, request, *args, **kwargs):
        file_obj = request.data.get("file", None)
        chunk_index = int(request.data.get("chunk_index", 0))
        upload_id = request.data.get("id", None)
        total_chunk = request.data.get("total_chunk", None)

        if file_obj is None:
            raise ValidationError({"file": ["This field is required."]})

        if total_chunk is None:
            raise ValidationError({"file": ["This field is required."]})

        total_chunk = int(total_chunk)

        if chunk_index + 1 > total_chunk:
            raise ValidationError("chunk index must be less than total chunk")

        if upload_id is not None:
            try:
                media_file = MediaFile.objects.get(upload_id=upload_id, user=request.user, total_chunk=total_chunk,
                                                   is_complete=False)

                if media_file.is_expire():
                    return Response(status=status.HTTP_410_GONE)

                if chunk_index != media_file.chunks_uploaded + 1:
                    return Response({"upload_id": media_file.upload_id, "chunk_index": media_file.chunks_uploaded + 1},
                                    status=status.HTTP_200_OK)

                file_path = media_file.file.path
                with open(file_path, 'ab') as f:
                    f.write(file_obj.read())

                media_file.chunks_uploaded = chunk_index
                media_file.save()

            except MediaFile.DoesNotExist:
                raise NotFound("file is not exist")
        else:
            if chunk_index != 0:
                raise ValidationError({"chunk_index": ["This field must be 0."]})
            media_file = MediaFile.objects.create(user=request.user, file=file_obj, total_chunk=total_chunk)

        if total_chunk == chunk_index + 1:
            media_file.is_complete = True
            media_file.save()
            return Response({"id": media_file.pk, "upload_id": media_file.upload_id, "is_complete": True},
                            status=status.HTTP_201_CREATED)

        return Response({"upload_id": media_file.upload_id, "chunk_index": media_file.chunks_uploaded + 1},
                        status=status.HTTP_200_OK)
