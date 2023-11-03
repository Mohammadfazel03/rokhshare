from django.db.models import *
from django.utils.translation import gettext_lazy as _

from user.models import User


def trailer_path_file(instance, filename):
    return f"trailer/{instance.pk}-{instance.name}-{filename}"


def media_thumbnail_path_file(instance, filename):
    return f"thumbnail/{instance.pk}-{instance.name}-{filename}"


def media_poster_path_file(instance, filename):
    return f"poster/{instance.pk}-{instance.name}-{filename}"


# Create your models here.
class Media(Model):
    class MediaType(TextChoices):
        FREE = "Free", _("Free")
        SUBSCRIPTION = "Subscription", _("Subscription")
        ADVERTISING = "Advertising", _("Advertising")

    name = CharField(max_length=100)
    trailer = FileField(upload_to=trailer_path_file)
    synopsis = TextField()
    thumbnail = ImageField(upload_to=media_thumbnail_path_file)
    poster = ImageField(upload_to=media_poster_path_file)
    value = CharField(max_length=15, choices=MediaType.choices, default=MediaType.FREE)
    release_date = DateTimeField()


def movie_path_file(instance, filename):
    return f"movie/{instance.media.pk}-{instance.media.name}-{filename}"


class Movie(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    video = FileField(upload_to=movie_path_file)
    time = IntegerField()


class TvSeries(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    season_number = IntegerField()


class Season(Model):
    series = ForeignKey(TvSeries, on_delete=CASCADE)
    number = IntegerField()


def episode_path_file(instance, filename):
    return f"movie/{instance.season.series.media.pk}" \
           f"-S{instance.season.number}-E{instance.number}" \
           f"-{instance.name}-{filename}"


class Episode(Model):
    season = ForeignKey(Season, on_delete=CASCADE)
    number = IntegerField()
    name = CharField(max_length=100)
    video = FileField(upload_to=episode_path_file)
    time = IntegerField()
    synopsis = TextField()


def genre_poster_path_file(instance, filename):
    return f"genre-poster/{instance.pk}-{instance.title}-{filename}"


class Genre(Model):
    title = CharField(max_length=100)
    poster = ImageField(upload_to=genre_poster_path_file)


class GenreMedia(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    genre = ForeignKey(Genre, on_delete=CASCADE)


def country_flag_path_file(instance, filename):
    return f"country-flag/{instance.pk}-{instance.name}-{filename}"


class Country(Model):
    name = CharField(max_length=100)
    flag = ImageField(upload_to=country_flag_path_file)


class CountryMedia(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    country = ForeignKey(Country, on_delete=CASCADE)


def gallery_path_file(instance, filename):
    return f"gallery/{instance.pk}-{filename}"


class MediaGallery(Model):
    file = FileField(upload_to=gallery_path_file)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)


def artist_path_file(instance, filename):
    return f"artists/{instance.pk}-{instance.name}-{filename}"


class Artist(Model):
    name = CharField(max_length=100)
    biography = TextField()
    image = ImageField(upload_to=artist_path_file)


class Cast(Model):
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    artist = ForeignKey(Artist, on_delete=CASCADE, null=False)


class Slider(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    description = TextField()
    title = CharField(max_length=250)
    priority = IntegerField()


def collection_poster_path_file(instance, filename):
    return f"collection-poster/{instance.pk}-{instance.name}-{filename}"


class Collection(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    name = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    is_private = BooleanField()
    is_confirm = BooleanField()
    poster = ImageField(upload_to=collection_poster_path_file)


class Comment(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    comment = TextField()
    title = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    is_confirm = BooleanField()


class Rating(Model):
    rating = SmallIntegerField()
    user = ForeignKey(User, on_delete=CASCADE)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    created_at = DateTimeField(auto_now_add=True)


class SeenMedia(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    created_at = DateTimeField(auto_now_add=True)
