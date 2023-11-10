from rest_framework import fields
from rest_framework.serializers import *
from django.db import transaction
from movie.models import Genre, Country, Artist, Media, Movie, Cast, GenreMedia, CountryMedia


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

        if Artist.objects.filter(pk=js['artist_id']).exists():
            raise ValidationError()


class MovieSerializer(Serializer):
    casts = fields.JSONField(read_only=False, validators=[cast_validator], required=False)
    genres = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Genre.objects.all())
    countries = PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Country.objects.all())
    release_date = fields.DateTimeField(input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'])
    name = CharField(max_length=100)
    trailer = FileField()
    synopsis = fields.CharField()
    thumbnail = ImageField()
    poster = ImageField()
    value = ChoiceField(choices=['Free', 'Subscription', 'Advertising'], allow_null=False, allow_blank=False)
    video = FileField()
    time = IntegerField()

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

        movie.casts.set(casts)
        return validated_data
