from rest_framework import fields
from rest_framework.serializers import *
from django.db import transaction
from movie.models import Genre, Country, Artist, Media, Movie, Cast, GenreMedia, CountryMedia, TvSeries


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

    class Meta:
        model = Movie
        fields = "__all__"
        lookup_field = "media__id"


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

    class Meta:
        model = TvSeries
        fields = "__all__"
        lookup_field = "media__id"
