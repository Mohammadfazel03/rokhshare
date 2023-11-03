from django.db import models

from movie.models import Movie, Episode
from user.models import User


def advertise_path(instance, filename):
    return f'advertise/{instance.pk}-{filename}'


# Create your models here.
class Advertise(models.Model):
    title = models.CharField(max_length=100)
    time = models.IntegerField()
    video = models.FileField(upload_to=advertise_path)
    created_at = models.DateTimeField(auto_now_add=True)
    number_repeated = models.IntegerField()


class AdvertiseSeen(models.Model):
    advertise = models.ForeignKey(Advertise, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    times = models.IntegerField()
