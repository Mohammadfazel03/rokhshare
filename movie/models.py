import uuid
from datetime import timedelta

from django.db.models import *
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from user.models import User
from django.utils.crypto import get_random_string


def trailer_path_file(instance, filename):
    return f"trailer/{get_random_string(length=8)}-{instance.name}-{filename}"


def media_thumbnail_path_file(instance, filename):
    return f"thumbnail/{get_random_string(length=8)}-{instance.name}-{filename}"


def media_poster_path_file(instance, filename):
    return f"poster/{get_random_string(length=8)}-{instance.name}-{filename}"


# Create your models here.
class Media(Model):
    class MediaType(TextChoices):
        FREE = "Free", _("Free")
        SUBSCRIPTION = "Subscription", _("Subscription")
        ADVERTISING = "Advertising", _("Advertising")

    name = CharField(max_length=100)
    trailer = OneToOneField('MediaFile', on_delete=CASCADE)
    synopsis = TextField()
    thumbnail = ImageField(upload_to=media_thumbnail_path_file)
    poster = ImageField(upload_to=media_poster_path_file)
    value = CharField(max_length=15, choices=MediaType.choices, default=MediaType.FREE)
    release_date = DateTimeField()
    genres = ManyToManyField('Genre', through='GenreMedia')
    countries = ManyToManyField('Country', through='CountryMedia')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.trailer:
            self.trailer.delete()
        self.poster.delete(save=False)
        self.thumbnail.delete(save=False)


def movie_path_file(instance, filename):
    return f"movie-video/{instance.media.pk}-{instance.media.name}-{filename}"


class Movie(Model):
    media = OneToOneField(Media, on_delete=CASCADE)
    video = OneToOneField('MediaFile', on_delete=CASCADE)
    time = IntegerField()
    casts = ManyToManyField('Artist', through='Cast')

    def delete(self, *args, **kwargs):
        if self.media:
            self.media.delete()
        if self.video:
            self.video.delete()
        super().delete(*args, **kwargs)


class TvSeries(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    season_number = IntegerField()


class Season(Model):
    series = ForeignKey(TvSeries, on_delete=CASCADE)
    number = IntegerField()


def episode_path_file(instance, filename):
    return f"movie-video/{instance.season.series.media.pk}" \
           f"-S{instance.season.number}-E{instance.number}" \
           f"-{instance.name}-{filename}"


class Episode(Model):
    season = ForeignKey(Season, on_delete=CASCADE)
    number = IntegerField()
    name = CharField(max_length=100)
    video = FileField(upload_to=episode_path_file)
    time = IntegerField()
    synopsis = TextField()
    casts = ManyToManyField('Artist', through='Cast')


def genre_poster_path_file(instance, filename):
    return f"genre-poster/{get_random_string(length=8)}-{instance.title}-{filename}"


class Genre(Model):
    title = CharField(max_length=100)
    poster = ImageField(upload_to=genre_poster_path_file)


class GenreMedia(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    genre = ForeignKey(Genre, on_delete=CASCADE)


def country_flag_path_file(instance, filename):
    return f"country-flag/{get_random_string(length=8)}-{instance.name}-{filename}"


class Country(Model):
    name = CharField(max_length=100)
    flag = ImageField(upload_to=country_flag_path_file)


class CountryMedia(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    country = ForeignKey(Country, on_delete=CASCADE)


def gallery_path_file(instance, filename):
    return f"gallery/{get_random_string(length=8)}-{filename}"


class MediaGallery(Model):
    file = FileField(upload_to=gallery_path_file)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)


def artist_path_file(instance, filename):
    return f"artists/{get_random_string(length=8)}-{instance.name}-{filename}"


class Artist(Model):
    name = CharField(max_length=100)
    biography = TextField()
    image = ImageField(upload_to=artist_path_file)


class Cast(Model):
    class CastPosition(TextChoices):
        OTHER = "Other", _("Other")
        ACTOR = "Actor", _("Actor")
        DIRECTOR = "Director", _("Director")
        PRODUCER = "Producer", _("Producer")
        WRITER = "Writer", _("Writer")
        EDITOR = "Editor", _("Editor")
        EXECUTOR_OF_PLAN = "Executor Of Plan", _("Executor Of Plan")
        PRODUCTION_MANAGER = "Production Manager", _("Production Manager")
        DIRECTOR_OF_FILMING_MANAGER = "Director Of Filming Manager", _("Production Manager")

    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    artist = ForeignKey(Artist, on_delete=CASCADE, null=False)
    position = CharField(max_length=50, choices=CastPosition.choices, default=CastPosition.OTHER)


class Slider(Model):
    media = ForeignKey(Media, on_delete=CASCADE)
    description = TextField()
    title = CharField(max_length=250)
    priority = IntegerField()


def collection_poster_path_file(instance, filename):
    return f"collection-poster/{get_random_string(length=8)}-{instance.name}-{filename}"


class Collection(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    name = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    is_private = BooleanField(default=False)
    is_confirm = BooleanField(default=False)
    poster = ImageField(upload_to=collection_poster_path_file)
    media = ManyToManyField(Media, through='CollectionMedia')


class Comment(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    media = ForeignKey(Media, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    comment = TextField()
    title = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    is_confirm = BooleanField(default=False)


class Rating(Model):
    rating = SmallIntegerField()
    user = ForeignKey(User, on_delete=CASCADE)
    media = ForeignKey(Media, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    created_at = DateTimeField(auto_now_add=True)


class SeenMedia(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    movie = ForeignKey(Movie, on_delete=CASCADE, null=True)
    episode = ForeignKey(Episode, on_delete=CASCADE, null=True)
    created_at = DateTimeField(auto_now_add=True)


class CollectionMedia(Model):
    collection = ForeignKey(Collection, on_delete=CASCADE)
    media = ForeignKey(Media, on_delete=CASCADE)


def generate_upload_id():
    return uuid.uuid4().hex


def media_file_filename(instance, filename):
    return f"{get_random_string(length=24)}-{filename}"


class MediaFile(Model):
    upload_id = CharField(max_length=32, unique=True, editable=False,
                          default=generate_upload_id)
    user = ForeignKey(User, on_delete=DO_NOTHING, blank=False, null=False)
    file = FileField(upload_to=media_file_filename)
    uploaded_on = DateTimeField(auto_now_add=True)
    chunks_uploaded = IntegerField(default=0)
    is_complete = BooleanField(default=False)
    total_chunk = IntegerField(null=False, blank=False)

    def delete(self, *args, **kwargs):
        super(MediaFile, self).delete(*args, **kwargs)
        if self.file:
            storage, path = self.file.storage, self.file.path
            storage.delete(path)

    def is_expire(self):
        return not self.is_complete and timedelta(hours=12) + self.uploaded_on < timezone.now()
