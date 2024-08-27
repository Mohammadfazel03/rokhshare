from django.db.models import Avg
from rest_framework.serializers import *
from django.db import transaction
from rest_framework.validators import UniqueValidator
from api.validators import MediaEpisodeValidator
from movie.models import Genre, Country, Artist, Media, Movie, Cast, GenreMedia, CountryMedia, TvSeries, Season, \
    Episode, MediaGallery, Slider, Collection, Comment, Rating, MediaFile
from user.models import User
from user.serializers import CommentUserSerializer


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

        if js['position'] not in Cast.CastPosition:
            raise ValidationError()

        if not Artist.objects.filter(pk=js['artist_id']).exists():
            raise ValidationError()


class CreateMovieSerializer(ModelSerializer):
    video = PrimaryKeyRelatedField(queryset=MediaFile.objects.filter(is_complete=True), many=False, allow_null=False,
                                   write_only=True)
    casts = JSONField(validators=[cast_validator], required=True, write_only=True)
    time = IntegerField(required=True, write_only=True)
    genres = PrimaryKeyRelatedField(queryset=Genre.objects.filter(), write_only=True, many=True, allow_null=False)
    countries = PrimaryKeyRelatedField(queryset=Country.objects.filter(), write_only=True, many=True, allow_null=False)

    class Meta:
        model = Media
        fields = "__all__"

    def create(self, validated_data):
        casts = map(lambda c: Cast(position=c['position'], artist_id=c['artist_id']), validated_data['casts'])
        media = Media(release_date=validated_data['release_date'], name=validated_data['name'],
                      trailer=validated_data['trailer'], synopsis=validated_data['synopsis'],
                      thumbnail=validated_data['thumbnail'], poster=validated_data['poster'],
                      value=validated_data['value'])
        genres = map(lambda g: GenreMedia(genre=g), validated_data['genres'])
        countries = map(lambda c: CountryMedia(country=c), validated_data['countries'])
        movie = Movie(video=validated_data['video'], time=validated_data['time'])
        with transaction.atomic():
            media.save()
            movie.media = media
            movie.save()
            for cast in casts:
                cast.movie = movie
                cast.save()

            for genre in genres:
                genre.media = media
                genre.save()

            for country in countries:
                country.media = media
                country.save()

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
                old_values['video'] = instance.movie.video
                instance.movie.video = validated_data['video']

        if validated_data.get("time", None):
            instance.movie.time = validated_data['time']

        with transaction.atomic():
            if validated_data.get('casts', None):
                if len(validated_data.get('casts', None)) > 0:
                    instance.movie.casts.clear()
                    for cast in validated_data.get('casts', []):
                        Cast(artist_id=cast['artist_id'], position=cast['position'], movie_id=instance.movie.id).save()
            instance.save()

            for attr, value in m2m_fields:
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
        representation_serializer = MovieSerializer(instance=instance.movie)
        return representation_serializer.data


class MediaSerializer(ModelSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)
    trailer = MediaFileSerializer(read_only=True)

    class Meta:
        model = Media
        fields = "__all__"


class MovieSerializer(ModelSerializer):
    media = MediaSerializer(read_only=True)
    casts = CastSerializer(source='cast_set', read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)
    video = MediaFileSerializer(read_only=True)

    class Meta:
        model = Movie
        fields = "__all__"

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(media=obj.media).aggregate(Avg('rating'))['rating__avg']

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(media=obj.media, state=Comment.CommentState.ACCEPT)
                                 .order_by('-created_at')[:5], many=True).data


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
        genres = map(lambda g: GenreMedia(genre=g), validated_data.pop('genres'))
        countries = map(lambda c: CountryMedia(country=c), validated_data.pop('countries'))

        with transaction.atomic():
            media = Media.objects.create(**validated_data)
            TvSeries.objects.create(media=media)

            for genre in genres:
                genre.media = media
                genre.save()

            for country in countries:
                country.media = media
                country.save()

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
    casts = ArtistSerializer(read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)

    class Meta:
        model = TvSeries
        fields = "__all__"

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(media=obj.media).aggregate(Avg('rating', default=0))['rating__avg']

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(media=obj.media, state=Comment.CommentState.ACCEPT)
                                 .order_by('-created_at')[:5], many=True).data


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
        info = model_meta.get_field_info(instance)

        m2m_fields = []
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
        casts = validated_data.pop('casts', [])
        with transaction.atomic():
            instance = Episode.objects.create(**validated_data)
            for cast in casts:
                Cast(artist_id=cast['artist_id'], position=cast['position'], episode=instance).save()

            series = instance.season.series
            series.episode_number += 1
            series.save()

        return instance

    def update(self, instance, validated_data):
        old_values = {}
        raise_errors_on_nested_writes('update', self, validated_data)

        for attr, value in validated_data.items():
            if attr != 'season' and attr != 'casts':
                if attr in ('thumbnail', 'video', 'poster', 'trailer'):
                    old_values[attr] = getattr(instance, attr, None)

                if value is not None and type(value) == str and len(value) == 0:
                    value = None

                setattr(instance, attr, value)

        with transaction.atomic():
            if validated_data.get('casts', None):
                if len(validated_data.get('casts', None)) > 0:
                    instance.casts.clear()
                    for cast in validated_data.get('casts', []):
                        Cast(artist_id=cast['artist_id'], position=cast['position'], episode=instance).save()
            instance.save()

        for attr, item in old_values.items():
            if attr in ('poster', 'thumbnail'):
                item.delete(save=False)
            else:
                item.delete()

        return instance


class EpisodeSerializer(ModelSerializer):
    casts = ArtistSerializer(read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)
    comments_count = IntegerField(read_only=True, required=False)
    trailer = MediaFileSerializer(read_only=True)
    video = MediaFileSerializer(read_only=True)

    class Meta:
        model = Episode
        fields = "__all__"

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(episode=obj).aggregate(Avg('rating', default=0))['rating__avg']

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(episode=obj, state=Comment.CommentState.ACCEPT)
                                 .order_by('-created_at')[:5], many=True).data


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


class SliderMediaSerializer(ModelSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)

    class Meta:
        model = Media
        exclude = ('trailer', 'casts')


class SliderSerializer(ModelSerializer):
    media = SliderMediaSerializer(read_only=True)

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


class MediaInputSerializer(Serializer):
    media = PrimaryKeyRelatedField(many=True, queryset=Media.objects.all(), required=True, allow_null=False,
                                   allow_empty=False)


class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"

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
            instance = Rating.objects.get(media=validated_data.get('media'), user=validated_data['user'],
                                          episode=validated_data.get('episode'))
            instance = super().update(instance, validated_data)
        except Rating.DoesNotExist:
            instance = Rating.objects.create(**validated_data)

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
