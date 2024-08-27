import os
from datetime import timedelta
from io import BytesIO
from PIL import Image
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from magic import magic
from moviepy.video.io.VideoFileClip import VideoFileClip
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
from api.permissions import IsSuperUser, IsOwner, CollectionRetrievePermission
from movie.models import Genre, Artist, Country, Movie, TvSeries, Season, Episode, MediaGallery, Slider, Collection, \
    Media, Comment, Rating, SeenMedia, MediaFile
from movie.serializers import GenreSerializer, CountrySerializer, ArtistSerializer, CreateMovieSerializer, \
    MovieSerializer, SeriesSerializer, CreateSeriesSerializer, SeasonSerializer, EpisodeSerializer, \
    MediaGallerySerializer, SliderSerializer, CollectionSerializer, MediaInputSerializer, CreateCommentSerializer, \
    RatingSerializer, DashboardCommentSerializer, DashboardSliderSerializer, AdminMovieSerializer, \
    AdminTvSeriesSerializer, AdminCollectionSerializer, MediaFileSerializer, CommentSerializer, MyCommentSerializer, \
    UpdateCommentSerializer, CreateEpisodeSerializer, MediaSerializer, CreateSliderSerializer
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
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsSuperUser]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateMovieSerializer
        elif self.action in ['retrieve', 'list']:
            return MovieSerializer

    def get_queryset(self):
        if self.action in ['partial_update']:
            return Movie.objects.filter().select_related("media").order_by('-pk')
        elif self.action in ['destroy']:
            return Movie.objects.filter()
        elif self.action in ['retrieve', 'list']:
            return Movie.objects \
                .select_related("media", "video", "media__trailer") \
                .annotate(rating=Avg('media__rating__rating', default=0)) \
                .prefetch_related(Prefetch("media__casts", queryset=Cast.objects.select_related('artist')
                                           , to_attr='media_casts'), "media__countries", "media__genres"
                                  , Prefetch("media__comment_set",
                                             queryset=Comment.objects.filter(state=Comment.CommentState.ACCEPT)
                                             .order_by('-created_at')[:5], to_attr='comments')
                                  , Prefetch("media__mediagallery_set",
                                             queryset=MediaGallery.objects.order_by('-pk')[:5],
                                             to_attr='gallery')) \
                .order_by('-pk')

    def get_object(self):
        if self.action in ['partial_update']:
            return super().get_object().media
        return super().get_object()


class SeriesViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsSuperUser]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateSeriesSerializer
        elif self.action in ['retrieve', 'list']:
            return SeriesSerializer

    def get_queryset(self):
        if self.action in ['partial_update']:
            return TvSeries.objects.select_related("media").order_by('-pk')
        elif self.action == 'season':
            return TvSeries.objects.prefetch_related('season_set')
        if self.action in ['retrieve', 'list']:
            return TvSeries.objects.select_related("media", "media__trailer") \
                .annotate(rating=Avg('media__rating__rating', default=0)) \
                .prefetch_related(
                Prefetch("media__casts", queryset=Cast.objects.select_related('artist').distinct('artist', 'position')
                         , to_attr='media_casts'), "media__countries", "media__genres",
                Prefetch("media__comment_set",
                         queryset=Comment.objects.filter(state=Comment.CommentState.ACCEPT)
                         .order_by('-created_at')[:5], to_attr='comments'),
                Prefetch("media__mediagallery_set",
                         queryset=MediaGallery.objects.order_by('-pk')[:5],
                         to_attr='gallery')) \
                .order_by('-pk')

        else:
            return TvSeries.objects.filter()

    def get_object(self):
        if self.action in ['partial_update']:
            return super().get_object().media
        return super().get_object()

    @action(methods=['GET'], detail=True, url_path='season', url_name='season')
    def season(self, request, pk):
        queryset = Season.objects.filter(series_id=pk).annotate(episode_number=Count("episode")).order_by("-number")
        page = self.paginate_queryset(queryset)
        serializer = SeasonSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class SeasonViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = SeasonSerializer
    queryset = Season.objects.all()

    @action(methods=['GET'], detail=True, url_path='episode', url_name='episode')
    def episode(self, request, pk):
        queryset = self.get_object().episode_set.annotate(comments_count=Count("comment")).filter().order_by("-number")
        page = self.paginate_queryset(queryset)
        serializer = EpisodeSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class EpisodeViewSet(ModelViewSet):
    permission_classes = [IsSuperUser]
    queryset = Episode.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateEpisodeSerializer
        elif self.action in ['retrieve', 'list']:
            return EpisodeSerializer

    @action(methods=['GET'], detail=True, url_path='gallery', url_name='gallery')
    def gallery(self, request, pk):
        queryset = MediaGallery.objects.filter(episode=pk).select_related('file').order_by("-pk")
        page = self.paginate_queryset(queryset)
        serializer = MediaGallerySerializer(page, many=True, context={
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        })
        return self.get_paginated_response(serializer.data)


class MediaGalleryViewSet(mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          GenericViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = MediaGallerySerializer
    queryset = MediaGallery.objects.select_related('file').all()

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsSuperUser()]


class SliderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [AllowAny()]
        return [IsSuperUser()]

    def get_queryset(self):
        if self.action in ['retrieve', 'list']:
            return Slider.objects.select_related('media').prefetch_related('media__genres', 'media__countries')
        return Slider.objects.filter()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateSliderSerializer
        elif self.action in ['retrieve', 'list']:
            return SliderSerializer


class CollectionViewSet(ModelViewSet):
    serializer_class = CollectionSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        elif self.action == 'retrieve':
            return [CollectionRetrievePermission()]
        elif self.action in ['me_collection', 'create']:
            return [IsAuthenticated()]
        elif self.action == 'change_state':
            return [IsSuperUser()]

        return [IsOwner()]

    def get_queryset(self):
        if self.action == 'list':
            return Collection.objects.filter(state=Collection.CollectionState.ACCEPT, is_private=False).order_by('-last_update')
        elif self.action == 'media':
            return Collection.objects.prefetch_related('media').filter()
        return Collection.objects.filter()

    @action(methods=['POST'], detail=True, url_path='state', url_name='state')
    def change_state(self, request, pk):
        state = request.data.get('state', None)

        if state is None:
            raise ValidationError(
                {'state': 'This field is required'}
            )

        try:
            if int(state) not in Collection.CollectionState:
                raise ValidationError(
                    {'state': f'{state} is not a valid choice.'}
                )
        except (TypeError, ValueError):
            raise ValidationError(
                {'state': f'{state} is not a valid choice.'}
            )

        collection = self.get_object()

        collection.state = state
        collection.save()

        return Response(data=CollectionSerializer(instance=collection).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_name='my_collection', url_path='me')
    def me_collection(self, request):
        queryset = Collection.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=True, url_name='media', url_path='media')
    def media(self, request, pk):
        queryset = Media.objects.filter(collection=pk).order_by('-collectionmedia__pk')
        page = self.paginate_queryset(queryset)
        serializer = MediaSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['post'], detail=True, url_path='add', url_name='add')
    def add_media(self, request, pk):
        collection: Collection = self.get_object()
        media_serializer = MediaInputSerializer(data=request.data)
        media_serializer.is_valid(raise_exception=True)
        for media in media_serializer.validated_data['media']:
            collection.media.add(media)
        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='remove', url_name='remove')
    def remove_media(self, request, pk):
        collection: Collection = self.get_object()
        media_serializer = MediaInputSerializer(data=request.data)
        media_serializer.is_valid(raise_exception=True)
        for media in media_serializer.data['media']:
            collection.media.remove(media)

        collection.save()

        return Response(data={"message": "ok"}, status=status.HTTP_200_OK)


class CommentViewSet(mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Comment.objects.filter().order_by('-pk')

    def get_permissions(self):
        if self.action == 'list' or self.action == 'confirm_comment' or self.action == 'media_comment':
            return [IsSuperUser()]
        elif self.action == 'create' or self.action == 'my_comment':
            return [IsAuthenticated()]

        return [IsOwner()]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'media_comment' or self.action == 'episode_comment':
            return CommentSerializer
        elif self.action == 'create':
            return CreateCommentSerializer
        elif self.action == 'my_comment':
            return MyCommentSerializer

        return UpdateCommentSerializer

    @action(methods=['POST'], detail=True, url_path='state', url_name='state')
    def change_state(self, request, pk):
        state = request.data.get('state', None)

        if state is None:
            raise ValidationError(
                {'state': 'This field is required'}
            )

        try:
            if int(state) not in Comment.CommentState:
                raise ValidationError(
                    {'state': f'{state} is not a valid choice.'}
                )
        except (TypeError, ValueError):
            raise ValidationError(
                {'state': f'{state} is not a valid choice.'}
            )

        comment = self.get_object()

        comment.state = state
        comment.save()

        return Response(data=UpdateCommentSerializer(instance=comment).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_name='my_comment', url_path='my')
    def my_comment(self, request):
        queryset = Comment.objects.filter(user=request.user).select_related('media').select_related('episode').order_by(
            '-pk')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_name='media_comment', url_path='media/(?P<pk>[0-9]+)')
    def media_comment(self, request, pk):
        queryset = Comment.objects.filter(user=request.user, media__pk=pk).order_by('-pk')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer)

    @action(methods=['get'], detail=False, url_name='episode_comment', url_path='episode/(?P<pk>[0-9]+)')
    def episode_comment(self, request, pk):
        queryset = Comment.objects.filter(user=request.user, episode__pk=pk).order_by('-pk')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer)


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
        series = TvSeries.objects.select_related('media').order_by('-pk')
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
        ).order_by('-can_edit', '-last_update')
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
            mimetype = magic.from_file(media_file.file.path, mime=True)
            media_file.mimetype = mimetype
            if "video" in mimetype:
                try:
                    video = VideoFileClip(media_file.file.path)
                    thumb_temp = video.get_frame(video.duration * 0.3 if video.duration * 0.3 < 5 else 5)
                    image = Image.fromarray(thumb_temp)
                    thumbnail_buffer = BytesIO()
                    image.save(thumbnail_buffer, format='JPEG')
                    thumbnail_buffer.seek(0)
                    media_file.thumbnail.save(name=os.path.splitext(media_file.file.name)[0] + ".jpeg",
                                              content=thumbnail_buffer)
                    thumbnail_buffer.close()
                    video.close()
                except Exception:
                    pass

            media_file.save()
            return Response({"id": media_file.pk, "upload_id": media_file.upload_id, "is_complete": True},
                            status=status.HTTP_201_CREATED)

        return Response({"upload_id": media_file.upload_id, "chunk_index": media_file.chunks_uploaded + 1},
                        status=status.HTTP_200_OK)


class MediaViewSet(GenericViewSet, mixins.ListModelMixin):
    permission_classes = [IsSuperUser]
    serializer_class = MediaSerializer
    queryset = Media.objects.filter().order_by('-pk')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'id', 'synopsis']

    @action(methods=['GET'], detail=True, url_path='gallery', url_name='gallery')
    def gallery(self, request, pk):
        queryset = MediaGallery.objects.filter(media_id=pk).select_related('file').order_by("-pk")
        page = self.paginate_queryset(queryset)
        serializer = MediaGallerySerializer(page, many=True, context={
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        })
        return self.get_paginated_response(serializer.data)
