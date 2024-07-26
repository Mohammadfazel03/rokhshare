from django.db.models import Avg
from rest_framework import fields
from rest_framework.serializers import *
from django.db import transaction
from rest_framework.validators import UniqueValidator

from movie.models import Genre, Country, Artist, Media, Movie, Cast, GenreMedia, CountryMedia, TvSeries, Season, \
    Episode, MediaGallery, Slider, Collection, Comment, Rating, MediaFile
from user.models import User


class CommentSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(many=False, required=True, write_only=True, queryset=User.objects.all())

    class Meta:
        model = Comment
        fields = "__all__"

    def is_valid(self, raise_exception=False):
        res = super().is_valid(raise_exception=raise_exception)
        if self.initial_data.get('media', None) is None and self.initial_data.get('episode', None) is None:
            raise ValidationError("cant both media and episode be null")
        elif self.initial_data.get('media', None) is not None and self.initial_data.get('episode', None) is not None:
            raise ValidationError("cant both media and episode be fill")
        return res


class DashboardCommentMediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ("name", 'poster')


class DashboardCommentSerializer(ModelSerializer):
    username = CharField(source='user.username', read_only=True)
    media = DashboardCommentMediaSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('comment', 'created_at', "is_confirm", "username", "media")

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


def cast_validator(value):
    if type(value) is not list:
        raise ValidationError()

    for js in value:
        if type(js) is not dict:
            raise ValidationError()

        if 'artist_id' not in js or 'position' not in js:
            raise ValidationError()

        if not Artist.objects.filter(pk=js['artist_id']).exists():
            raise ValidationError()


class CreateMovieSerializer(Serializer):
    casts = fields.JSONField(read_only=False, validators=[cast_validator], required=False)
    genres = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Genre.objects.all())
    countries = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Country.objects.all())
    release_date = fields.DateTimeField(input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'], allow_null=False)
    name = CharField(max_length=100, allow_null=False, allow_blank=False)
    trailer = FileField(allow_null=False, allow_empty_file=False)
    synopsis = fields.CharField(allow_null=False, allow_blank=False)
    thumbnail = ImageField(allow_null=False, allow_empty_file=False)
    poster = ImageField(allow_null=False, allow_empty_file=False)
    value = ChoiceField(choices=['Free', 'Subscription', 'Advertising'], allow_null=False, allow_blank=False)
    video = FileField(allow_empty_file=False, allow_null=False)
    time = IntegerField(allow_null=False)

    def create(self, validated_data):
        media = Media(release_date=validated_data['release_date'], name=validated_data['name'],
                      trailer=validated_data['trailer'], synopsis=validated_data['synopsis'],
                      thumbnail=validated_data['thumbnail'], poster=validated_data['poster'],
                      value=validated_data['value'])
        movie = Movie(video=validated_data['video'], time=validated_data['time'])
        casts = map(lambda c: Cast(position=c['position'], artist_id=c['artist_id']), validated_data['casts'])
        genres = map(lambda g: GenreMedia(genre=g), validated_data['genres'])
        countries = map(lambda g: CountryMedia(country=g), validated_data['countries'])

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

        return validated_data

    def update(self, instance, validated_data):

        if validated_data.get("release_date", None):
            instance.media.release_date = validated_data['release_date']

        if validated_data.get("name", None):
            instance.media.name = validated_data['name']

        if validated_data.get("trailer", None):
            instance.media.trailer = validated_data['trailer']

        if validated_data.get("synopsis", None):
            instance.media.synopsis = validated_data['synopsis']

        if validated_data.get("thumbnail", None):
            instance.media.thumbnail = validated_data['thumbnail']

        if validated_data.get("poster", None):
            instance.media.poster = validated_data['poster']

        if validated_data.get("value", None):
            instance.media.value = validated_data['value']

        if validated_data.get("video", None):
            instance.video = validated_data['video']

        if validated_data.get("time", None):
            instance.time = validated_data['time']

        with transaction.atomic():
            if validated_data.get('genres', None):
                instance.media.genres.clear()
                for genre in validated_data.get('genres', []):
                    GenreMedia(genre=genre, media=instance.media).save()

            if validated_data.get('countries', None):
                instance.media.countries.clear()
                for country in validated_data.get('countries', []):
                    CountryMedia(country=country, media=instance.media).save()

            if validated_data.get('casts', None):
                instance.casts.clear()
                for cast in validated_data.get('casts', []):
                    Cast(artist_id=cast['artist_id'], position=cast['position'], movie_id=instance.id).save()

            instance.media.save()
            instance.save()

        return CreateMovieSerializer()


class MediaSerializer(ModelSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    countries = CountrySerializer(read_only=True, many=True)

    class Meta:
        model = Media
        fields = "__all__"
        lookup_field = "id"


class MovieSerializer(ModelSerializer):
    media = MediaSerializer(read_only=True)
    casts = ArtistSerializer(read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)

    class Meta:
        model = Movie
        fields = "__all__"
        lookup_field = "media__id"

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(media=obj.media).aggregate(Avg('rating'))['rating__avg']

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(media=obj.media, is_confirm=True).order_by('-created_at')[:5],
                                 many=True).data


class CreateSerialSerializer(ModelSerializer):
    season_number = IntegerField(allow_null=False, write_only=True)
    genres = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Genre.objects.all())
    countries = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Country.objects.all())

    class Meta:
        model = Media
        fields = "__all__"
        lookup_field = "id"

    def create(self, validated_data):
        with transaction.atomic():
            genres = validated_data.pop("genres")
            countries = validated_data.pop("countries")
            season_number = validated_data.pop("season_number")
            media = Media.objects.create(**validated_data)
            TvSeries.objects.create(media=media, season_number=season_number)

            for genre in genres:
                GenreMedia.objects.create(genre=genre, media=media)

            for country in countries:
                CountryMedia.objects.create(country=country, media=media)

        return media

    def update(self, instance, validated_data):

        if validated_data.get("release_date", None):
            instance.media.release_date = validated_data['release_date']

        if validated_data.get("name", None):
            instance.media.name = validated_data['name']

        if validated_data.get("trailer", None):
            instance.media.trailer = validated_data['trailer']

        if validated_data.get("synopsis", None):
            instance.media.synopsis = validated_data['synopsis']

        if validated_data.get("thumbnail", None):
            instance.media.thumbnail = validated_data['thumbnail']

        if validated_data.get("poster", None):
            instance.media.poster = validated_data['poster']

        if validated_data.get("value", None):
            instance.media.value = validated_data['value']

        if validated_data.get("season_number", None):
            instance.season_number = validated_data['season_number']

        with transaction.atomic():
            if validated_data.get('genres', None):
                instance.media.genres.clear()
                for genre in validated_data.get('genres', []):
                    GenreMedia(genre=genre, media=instance.media).save()

            if validated_data.get('countries', None):
                instance.media.countries.clear()
                for country in validated_data.get('countries', []):
                    CountryMedia(country=country, media=instance.media).save()

            instance.media.save()
            instance.save()

        return CreateMovieSerializer()


class SerialSerializer(ModelSerializer):
    media = MediaSerializer(read_only=True)
    casts = ArtistSerializer(read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)

    class Meta:
        model = TvSeries
        fields = "__all__"
        lookup_field = "media__id"

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(media=obj.media).aggregate(Avg('rating'))['rating__avg']

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(media=obj.media, is_confirm=True).order_by('-created_at')[:5],
                                 many=True).data


class SeasonSerializer(ModelSerializer):
    class Meta:
        model = Season
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Season.objects.all(),
                fields=['series', 'number']
            )
        ]


class EpisodeSerializer(ModelSerializer):
    casts = ArtistSerializer(read_only=True, many=True)
    rating = SerializerMethodField(read_only=True)
    comments = SerializerMethodField(read_only=True)

    class Meta:
        model = Episode
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Episode.objects.all(),
                fields=['season', 'number']
            )
        ]

    @staticmethod
    def get_rating(obj):
        return Rating.objects.filter(episode=obj).aggregate(Avg('rating'))['rating__avg']

    def create(self, validated_data):
        casts = validated_data.pop('casts', [])
        with transaction.atomic():
            instance = Episode.objects.create(**validated_data)
            for cast in casts:
                Cast(artist_id=cast['artist_id'], position=cast['position'], episode=instance).save()

        return validated_data

    def update(self, instance, validated_data):
        casts = validated_data.pop('casts', [])

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if len(casts) > 0:
                instance.casts.clear()
                for cast in casts:
                    Cast(artist_id=cast['artist_id'], position=cast['position'], episode_id=instance.id).save()

        return instance

    @staticmethod
    def get_comments(obj):
        return CommentSerializer(Comment.objects.filter(episode=obj, is_confirm=True).order_by('-created_at')[:5],
                                 many=True).data


class MediaGallerySerializer(ModelSerializer):
    class Meta:
        model = MediaGallery
        fields = "__all__"

    def is_valid(self, raise_exception=False):
        if not self.initial_data.get('movie', None) and not self.initial_data.get('episode', None):
            raise ValidationError("cant both movie and episode be null")
        return super().is_valid(raise_exception=raise_exception)


class SliderSerializer(ModelSerializer):
    priority = IntegerField(validators=[UniqueValidator(queryset=Slider.objects.all())])

    # media = MediaSerializer(read_only=True)

    class Meta:
        model = Slider
        fields = "__all__"

    def to_representation(self, instance):
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                if field.field_name == 'media':
                    media = Media.objects.get(id=field.to_representation(attribute))
                    media_serializer = MediaSerializer(media)
                    ret[field.field_name] = media_serializer.to_representation(media_serializer.data)
                else:
                    ret[field.field_name] = field.to_representation(attribute)

        return ret


class CollectionSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(many=False, required=True, write_only=True, queryset=User.objects.all())

    class Meta:
        model = Collection
        exclude = ['media']


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


class MediaFileSerializer(ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ('file', 'uploaded_on')
