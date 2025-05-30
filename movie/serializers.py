from django.db.models import Prefetch
from rest_framework.serializers import *
from django.db import transaction
from rest_framework.validators import UniqueValidator
from api.validators import MediaEpisodeValidator
from movie.models import Genre, Country, Artist, Media, Movie, Cast, TvSeries, Season, \
    Episode, MediaGallery, Slider, Collection, Comment, Rating, MediaFile
from user.serializers import CommentUserSerializer
from api.pagination import CustomPageNumberPagination
from moviepy import VideoFileClip


class CreateCommentSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ('id', 'user', 'media', 'episode', 'parent', 'title', 'comment')
        validators = [
            MediaEpisodeValidator()
        ]
        extra_kwargs = {
            'media': {'write_only': True},
            'episode': {'write_only': True},
            'parent': {'write_only': True},
        }

    def validate(self, attrs):
        if attrs.get('parent', None):
            if attrs['parent'].media != attrs.get('media', None) \
                    or attrs['parent'].episode != attrs.get('episode', None):
                raise ValidationError("The replay comment is not correct")

        return attrs


class UpdateCommentSerializer(ModelSerializer):
    state = ChoiceField(choices=Comment.CommentState)

    class Meta:
        model = Comment
        fields = ('id', 'title', 'comment', 'state')

    def update(self, instance, validated_data):
        instance.state = Comment.CommentState.PENDING
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CommentEpisodeSerializer(ModelSerializer):
    season = SlugRelatedField(slug_field='number', read_only=True)

    class Meta:
        model = Episode
        fields = ('id', 'number', 'name', 'season')
        read_only_fields = ('number', 'name', 'season')


class CommentMediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ('id', 'poster', 'name')
        read_only_fields = ('poster', 'name')


class CommentSerializer(ModelSerializer):
    user = CommentUserSerializer()
    episode = CommentEpisodeSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'comment', 'title', 'created_at', 'state', 'episode')
        read_only_fields = ('user', 'comment', 'title', 'created_at', 'state', 'episode')


class MyCommentSerializer(ModelSerializer):
    parent = CommentSerializer(read_only=True)
    media = CommentMediaSerializer(read_only=True)
    episode = CommentEpisodeSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'comment', 'parent', 'title', 'created_at', 'state', 'media', 'episode')
        read_only_fields = ('comment', 'parent', 'title', 'created_at', 'state', 'media', 'episode')


class DashboardCommentMediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ("name", 'poster')


class DashboardCommentSerializer(ModelSerializer):
    username = CharField(source='user.username', read_only=True)
    media = DashboardCommentMediaSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('comment', 'created_at', "state", "username", "media")

    def to_representation(self, instance):
        if instance.media is None:
            media = Media.objects.filter(tvseries__season__episode=instance.episode).get()
            instance.media = media

        return super().to_representation(instance)


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class CountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class ArtistSerializer(ModelSerializer):
    class Meta:
        model = Artist
        fields = "__all__"


class MediaFileSerializer(ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['file', 'id', 'mimetype', 'thumbnail']


class MediaGallerySerializer(ModelSerializer):
    file = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True),
                                  validators=[UniqueValidator(queryset=MediaGallery.objects.filter())],
                                  many=False, allow_null=False,
                                  write_only=True)
    media = IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = MediaGallery
        fields = "__all__"
        extra_kwargs = {
            'episode': {'write_only': True},
        }

    def validate(self, attrs):
        episode = attrs.get('episode', None)
        media = attrs.get('media', None)

        if not media and not episode:
            raise ValidationError(detail={
                "media": ["at least one of media and episode must be set"],
                "episode": ["at least one of media and episode must be set"]
            })

        if media and episode:
            if media != Media.objects.get(tvseries__season__episode=episode):
                raise ValidationError(detail="The fields episode, media are not compatible with each other.")

        if not media and episode:
            attrs['media'] = Media.objects.get(tvseries__season__episode=episode)

        return attrs

    @staticmethod
    def validate_media(value):
        if value:
            media = Media.objects.get(pk=value)
            return media
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['file'] = MediaFileSerializer(instance=instance.file, context=self.context).data
        return ret


class CastSerializer(ModelSerializer):
    artist = ArtistSerializer(read_only=True, many=False)

    class Meta:
        model = Cast
        fields = ('artist', 'position')


def cast_validator(value):
    if type(value) is not list:
        raise ValidationError()

    for js in value:
        if type(js) is not dict:
            raise ValidationError()

        if 'artist_id' not in js or 'position' not in js:
            raise ValidationError()

        artist = None

        if js['position'] not in Cast.CastPosition:
            raise ValidationError()

        if isinstance(js['artist_id'], str):
            if str(js['artist_id']).isdigit():
                artist = int(js['artist_id'])

        if isinstance(js['artist_id'], int):
            artist = js['artist_id']

        if not artist:
            raise ValidationError()

        if not Artist.objects.filter(pk=artist).exists():
            raise ValidationError()


class CreateMovieSerializer(ModelSerializer):
    video = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True), many=False, allow_null=False,
                                   write_only=True)
    trailer = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True), many=False, allow_null=False,
                                     write_only=True)
    casts = JSONField(validators=[cast_validator], required=True, write_only=True)
    time = IntegerField(required=True, write_only=True)
    genres = PrimaryKeyRelatedField(queryset=Genre.objects.filter(), write_only=True, many=True, allow_null=False)
    countries = PrimaryKeyRelatedField(queryset=Country.objects.filter(), write_only=True, many=True, allow_null=False)

    class Meta:
        model = Media
        fields = "__all__"

    def create(self, validated_data):

        casts = map(lambda c: Cast(position=c['position'], artist_id=int(c['artist_id'])), validated_data.pop('casts'))
        time = validated_data.pop('time', 0)
        if time == 0:
            time = VideoFileClip(validated_data.get('video').file.path).duration

        movie = Movie(video=validated_data.pop('video'), time=time)
        countries = validated_data.pop('countries')
        genres = validated_data.pop('genres')
        media = Media(**validated_data)
        with transaction.atomic():
            media.save()
            movie.media = media
            movie.save()

            media.genres.set(genres)
            media.countries.set(countries)

            for cast in casts:
                cast.media = media
                cast.save()

        return media

    def update(self, instance, validated_data):
        old_values = {}

        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                if attr in ('thumbnail', 'trailer', 'poster'):
                    old_values[attr] = getattr(instance, attr, None)

                setattr(instance, attr, value)

        if validated_data.get("video", None):
            if instance.movie.video != validated_data['video']:
                time = validated_data.pop('time', 0)
                if time == 0:
                    time = VideoFileClip(validated_data.get('video').file.path).duration

                old_values['video'] = instance.movie.video
                instance.movie.video = validated_data['video']
                instance.movie.time = time


        with transaction.atomic():
            if validated_data.get('casts', None):
                if len(validated_data.get('casts', None)) > 0:
                    instance.casts.clear()
                    for cast in validated_data.get('casts', []):
                        Cast(artist_id=cast['artist_id'], position=cast['position'], media=instance).save()
            instance.save()

            for attr, value in m2m_fields:
                if attr != 'casts':
                    field = getattr(instance, attr)
                    field.set(value)

            instance.movie.save()

        for attr, item in old_values.items():
            if attr in ('poster', 'thumbnail'):
                item.delete(save=False)
            else:
                item.delete()

        return instance

    def to_representation(self, instance):
        representation_serializer = MediaMovieSerializer(instance=instance.movie)
        return representation_serializer.data


class MediaSerializer(ModelSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)
    trailer = MediaFileSerializer(read_only=True)

    class Meta:
        model = Media
        exclude = ['casts']


class MediaMovieSerializer(ModelSerializer):
    media = MediaSerializer(read_only=True, allow_null=False)
    rating = FloatField(read_only=True)
    comments = CommentSerializer(read_only=True, many=True)
    video = MediaFileSerializer(read_only=True)
    casts = CastSerializer(source="media.media_casts", read_only=True, many=True)
    gallery = MediaGallerySerializer(read_only=True, many=True)

    class Meta:
        model = Movie
        fields = "__all__"


class CreateSeriesSerializer(ModelSerializer):
    genres = PrimaryKeyRelatedField(queryset=Genre.objects.filter(), write_only=True, many=True, allow_null=False)
    countries = PrimaryKeyRelatedField(queryset=Country.objects.filter(), write_only=True, many=True,
                                       allow_null=False)
    trailer = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True), many=False, allow_null=False,
                                     write_only=True)

    class Meta:
        model = Media
        fields = "__all__"

    def create(self, validated_data):
        countries = validated_data.pop('countries')
        genres = validated_data.pop('genres')
        with transaction.atomic():
            media = Media.objects.create(**validated_data)
            TvSeries.objects.create(media=media)

            media.genres.set(genres)
            media.countries.set(countries)

        return media

    def update(self, instance, validated_data):
        old_values = {}

        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                if attr in ('thumbnail', 'trailer', 'poster'):
                    old_values[attr] = getattr(instance, attr, None)

                setattr(instance, attr, value)

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        for attr, item in old_values.items():
            if attr in ('poster', 'thumbnail'):
                item.delete(save=False)
            else:
                item.delete()

        return instance

    def to_representation(self, instance):
        representation_serializer = SeriesSerializer(instance=instance.tvseries)
        return representation_serializer.data


class SeriesSerializer(ModelSerializer):
    media = MediaSerializer(read_only=True)
    #### for postgresql
    # casts = CastSerializer(source="media.media_casts", read_only=True, many=True)
    #### for sqlite
    casts = SerializerMethodField()
    rating = FloatField(read_only=True)
    comments = CommentSerializer(read_only=True)
    gallery = MediaGallerySerializer(read_only=True, many=True)

    class Meta:
        model = TvSeries
        fields = "__all__"

    def get_casts(self, instance):
        q = Cast.objects.filter(media=instance.media).values('artist', 'position').distinct()
        return CastSerializer(
            map(lambda x: {'artist': Artist.objects.get(id=x['artist']), 'position': x['position']}, q.all()),
            many=True, context={**self.context}).data


class SeasonSerializer(ModelSerializer):
    episode_number = IntegerField(read_only=True, required=False)

    class Meta:
        model = Season
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Season.objects.all(),
                fields=['series', 'number']
            )
        ]

    def create(self, validated_data):
        with transaction.atomic():
            instance = Season.objects.create(**validated_data)
            instance.series.season_number += 1
            instance.series.save()
            return instance

    def update(self, instance, validated_data):
        old_values = {}

        raise_errors_on_nested_writes('update', self, validated_data)
        for attr, value in validated_data.items():
            if attr in ('thumbnail', 'poster'):
                old_values[attr] = getattr(instance, attr, None)

            if value is not None and type(value) == str and len(value) == 0:
                value = None
            setattr(instance, attr, value)

        instance.save()

        for attr, item in old_values.items():
            if attr in ('poster', 'thumbnail'):
                item.delete(save=False)
            else:
                item.delete()

        return instance


class CreateEpisodeSerializer(ModelSerializer):
    casts = JSONField(validators=[cast_validator], required=True, write_only=True)
    video = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True), many=False, allow_null=False,
                                   write_only=True)

    class Meta:
        model = Episode
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Episode.objects.all(),
                fields=['season', 'number']
            )
        ]

    def create(self, validated_data):
        casts = map(lambda c: Cast(position=c['position'], artist_id=int(c['artist_id'])), validated_data.pop('casts'))
        time = validated_data.pop('time', 0)
        if time == 0:
            time = VideoFileClip(validated_data.get('video').file.path).duration

        with transaction.atomic():
            instance = Episode.objects.create(**validated_data, time=time)
            media = Media.objects.get(tvseries__season=validated_data.get('season'))
            for cast in casts:
                cast.media = media
                cast.episode = instance
                cast.save()

            series = instance.season.series
            series.episode_number += 1
            series.save()

        return instance

    def update(self, instance, validated_data):
        old_values = {}
        raise_errors_on_nested_writes('update', self, validated_data)

        if validated_data.get("video", None):
            if instance.video != validated_data['video']:
                time = validated_data.pop('time', 0)
                if time == 0:
                    time = VideoFileClip(validated_data.get('video').file.path).duration

                old_values['video'] = instance.video
                instance.video = validated_data.pop('video')
                instance.time = time

        for attr, value in validated_data.items():
            if attr != 'season' and attr != 'casts':
                if attr in ('thumbnail', 'poster', 'trailer'):

                    old_values[attr] = getattr(instance, attr, None)

                if value is not None and type(value) == str and len(value) == 0:
                    value = None

                setattr(instance, attr, value)

        with transaction.atomic():
            if validated_data.get('casts', None):
                if len(validated_data.get('casts', None)) > 0:
                    media = Media.objects.get(tvseries__season__episode=instance)
                    instance.casts.clear()
                    for cast in validated_data.get('casts', []):
                        Cast(artist_id=cast['artist_id'], position=cast['position'], episode=instance,
                             media=media).save()
            instance.save()

        for attr, item in old_values.items():
            if attr in ('poster', 'thumbnail'):
                item.delete(save=False)
            else:
                item.delete()

        return instance


class EpisodeSerializer(ModelSerializer):
    casts = CastSerializer(source="media_casts", read_only=True, many=True)
    rating = FloatField(source='rating_avg', read_only=True)
    comments = CommentSerializer(read_only=True, many=True)
    comments_count = IntegerField(read_only=True, required=False)
    trailer = MediaFileSerializer(read_only=True)
    video = MediaFileSerializer(read_only=True)
    gallery = MediaGallerySerializer(read_only=True, many=True)

    class Meta:
        model = Episode
        fields = "__all__"


class SliderMediaSerializer(ModelSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)

    class Meta:
        model = Media
        exclude = ('trailer', 'casts')


class SliderSerializer(ModelSerializer):
    media = SliderMediaSerializer(read_only=True)
    rating = FloatField(allow_null=True)

    class Meta:
        model = Slider
        fields = "__all__"


class CreateSliderSerializer(ModelSerializer):
    priority = IntegerField(validators=[UniqueValidator(queryset=Slider.objects.all())])

    class Meta:
        model = Slider
        fields = "__all__"

    def to_representation(self, instance):
        return SliderSerializer(instance).data


class CollectionSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Collection
        exclude = ['media']
        read_only_fields = ('state', 'media')


class AppCollectionSerializer(ModelSerializer):
    media2 = SliderMediaSerializer(read_only=True, many=True)

    class Meta:
        model = Collection
        exclude = ['user', 'media', 'is_private', 'state']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['media'] = rep.pop('media2')
        return rep


class MediaInputSerializer(Serializer):
    media = PrimaryKeyRelatedField(many=True, queryset=Media.objects.all(), required=True, allow_null=False,
                                   allow_empty=False)


class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ['user']

    def validate_rating(self, value):
        if value > 10 or value < 0:
            raise ValidationError("out of range")
        return value

    def is_valid(self, raise_exception=False):
        res = super().is_valid(raise_exception=raise_exception)
        if self.initial_data.get('media', None) is None and self.initial_data.get('episode', None) is None:
            raise ValidationError("cant both media and episode be null")
        elif self.initial_data.get('media', None) is not None and self.initial_data.get('episode', None) is not None:
            raise ValidationError("cant both media and episode be fill")
        return res

    def create(self, validated_data):
        try:
            instance = Rating.objects.get(media=validated_data.get('media'), user=self.context.get('request').user,
                                          episode=validated_data.get('episode'))
            instance = super().update(instance, validated_data)
        except Rating.DoesNotExist:
            instance = Rating.objects.create(**validated_data, user=self.context.get('request').user)

        return instance


class DashboardSliderSerializer(ModelSerializer):
    media = DashboardCommentMediaSerializer(read_only=True)

    class Meta:
        model = Slider
        fields = "__all__"


class AdminMovieSerializer(ModelSerializer):
    name = CharField(source='media.name')
    release_date = DateTimeField(source='media.release_date')
    value = CharField(source='media.value')
    genres = GenreSerializer(source='media.genres', read_only=True, many=True)
    countries = CountrySerializer(source='media.countries', read_only=True, many=True)

    class Meta:
        model = Movie
        fields = ('name', 'genres', 'release_date', 'value', 'countries', 'id')


class AdminTvSeriesSerializer(ModelSerializer):
    name = CharField(source='media.name')
    release_date = DateTimeField(source='media.release_date')
    value = CharField(source='media.value')
    genres = GenreSerializer(source='media.genres', read_only=True, many=True)
    countries = CountrySerializer(source='media.countries', read_only=True, many=True)
    episode_number = IntegerField()

    class Meta:
        model = TvSeries
        fields = ('name', 'genres', 'release_date', 'value', 'countries', 'id', 'season_number', 'episode_number')


class AdminCollectionSerializer(ModelSerializer):
    owner = CharField(source="user.username")
    can_edit = BooleanField()

    class Meta:
        model = Collection
        exclude = ['media', 'is_private']

    def get_can_edit(self, obj):
        req = self.context.get('request')
        return req.user == obj.user if req else False


class SearchParamsSerializer(Serializer):
    query = CharField(max_length=200, required=False)
    media_type = ChoiceField(choices=['both', 'movie', 'series'], default='both', allow_blank=False, allow_null=False)
    genres = ListField(child=IntegerField(), allow_empty=False, allow_null=False, required=False)
    countries = ListField(child=IntegerField(), allow_empty=False, allow_null=False, required=False)
    start_date = IntegerField(min_value=1900, allow_null=False, required=False)
    end_date = IntegerField(allow_null=False, required=False)
    sort_by = ChoiceField(choices=['-name', 'name', '-release_date', 'release_date', '-rate', 'rate'],
                          default='-name', allow_blank=False, allow_null=False)

    def validate(self, attrs):
        if (attrs.get('start_date', None) is not None and attrs.get('end_date', None) is None) or (
                attrs.get('start_date', None) is None and attrs.get('end_date', None) is not None):
            raise ValidationError()

        if attrs.get('start_date', None) is not None and attrs.get('end_date', None) is not None:
            if attrs.get('start_date', None) >= attrs.get('end_date', None):
                raise ValidationError()

        return attrs


class MovieSerializer(ModelSerializer):
    # video = SerializerMethodField()

    class Meta:
        model = Movie
        exclude = ['media', 'video']

    # def get_video(self, instance):
    #     if not self.context.get('request').user.is_anonymous:
    #         if self.context.get('value') == Media.MediaType.FREE or self.context.get(
    #                 'value') == Media.MediaType.ADVERTISING or self.context.get('request').user.is_subscriber:
    #             return MediaFileSerializer(instance.video, context=self.context).data
    #
    #     return None


class RetrieveEpisodeSerializer(ModelSerializer):
    # video = SerializerMethodField()

    class Meta:
        model = Episode
        fields = ['id', 'name', 'number', 'time', 'synopsis', 'thumbnail', 'poster', 'publication_date']

    # def get_video(self, instance):
    #     if not self.context.get('request').user.is_anonymous:
    #         if self.context.get('value') == Media.MediaType.FREE or self.context.get(
    #                 'value') == Media.MediaType.ADVERTISING or self.context.get('request').user.is_subscriber:
    #             return MediaFileSerializer(instance.video, context=self.context).data
    #
    #     return None


class RetrieveSeasonSerializer(ModelSerializer):
    episodes = RetrieveEpisodeSerializer(many=True)
    episode_number = SerializerMethodField()

    class Meta:
        model = Season
        fields = ['id', 'name', 'number', 'episodes', 'episode_number']

    def get_episode_number(self, instance):
        return Episode.objects.filter(season=instance).count()


class RetrieveSeriesSerializer(ModelSerializer):
    seasons = RetrieveSeasonSerializer(many=True)

    class Meta:
        model = TvSeries
        exclude = ['media']


class RetrieveCommentSerializer(ModelSerializer):
    user = CommentUserSerializer()

    class Meta:
        model = Comment
        fields = ['title', 'comment', 'user', 'created_at']


class RetrieveMediaSerializer(ModelSerializer):
    total_comments = SerializerMethodField()
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)
    trailer = MediaFileSerializer(read_only=True)
    #### for postgresql
    # casts = CastSerializer(many=True)

    #### for sqlite
    casts = SerializerMethodField()
    comments = RetrieveCommentSerializer(many=True)
    rate = FloatField()

    class Meta:
        model = Media
        fields = '__all__'

    #### for sqlite
    def get_casts(self, instance):
        q = Cast.objects.filter(media=instance).values('artist', 'position').distinct()
        return CastSerializer(
            map(lambda x: {'artist': Artist.objects.get(id=x['artist']), 'position': x['position']}, q.all()),
            many=True, context={**self.context}).data

    def get_total_comments(self, instance):
        return Comment.objects.filter(media=instance, state=Comment.CommentState.ACCEPT).count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        is_movie = hasattr(instance, 'movie')
        rep['is_movie'] = is_movie
        rep['my_rate'] = None

        if not self.context.get('request').user.is_anonymous:
            rate = Rating.objects.filter(user=self.context.get('request').user, media=instance).first()
            if rate:
                rep['my_rate'] = rate.rating

        rep['is_premium'] = self.context.get('request').user.is_subscriber if not self.context.get(
            'request').user.is_anonymous else False
        if is_movie:
            movie = Movie.objects.select_related('video').get(media=instance)
            rep['movie'] = MovieSerializer(movie, context={**self.context, "value": instance.value}).data
        else:
            series = TvSeries.objects.prefetch_related(
                Prefetch("season_set", queryset=Season.objects.prefetch_related(
                    Prefetch('episode_set',
                             queryset=Episode.objects.order_by('number')[:CustomPageNumberPagination.page_size],
                             to_attr='episodes')).order_by(
                    'number')[:1], to_attr='seasons')
            ).get(media=instance)
            rep['series'] = RetrieveSeriesSerializer(series, context={**self.context, "value": instance.value}).data

        return rep


class MediaRateSerializer(Serializer):
    rating = IntegerField()
    count = IntegerField()


class MediaFilePlaySerializer(ModelSerializer):
    ads_time = SerializerMethodField()
    is_premium = SerializerMethodField()
    file = SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = ['file', 'id', 'mimetype', 'thumbnail', 'ads_time', 'is_premium']

    def get_is_premium(self, instance):
        return self.context.get('request').user.is_subscriber or self.context.get('media').value == Media.MediaType.FREE

    def get_file(self, instance):
        url = f'/api/v1/stream/{instance.pk}/file/'
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url

    def get_ads_time(self, instance):
        media = self.context.get('media')
        user = self.context.get('request').user
        video = VideoFileClip(instance.file.path)
        duration = video.duration

        if user.is_subscriber:
            return None

        if media.value == Media.MediaType.FREE:
            return [0]

        if media.value == Media.MediaType.ADVERTISING:
            if duration > 300:
                return [0, int(duration // 20), int(duration // 10), int(duration // 15), ]
            return [0]

        if media.value == Media.MediaType.SUBSCRIPTION:
            raise ValidationError()

        return [0]
