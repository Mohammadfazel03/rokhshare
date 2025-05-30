from django.db import models

from movie.models import Movie, Episode, MediaFile, Media
from user.models import User


def advertise_path(instance, filename):
    return f'advertise/{instance.pk}-{filename}'


# Create your models here.
class Advertise(models.Model):
    title = models.CharField(max_length=100)
    time = models.IntegerField()
    file = models.OneToOneField(MediaFile, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    number_repeated = models.IntegerField()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.file:
            self.file.delete()


class AdvertiseSeen(models.Model):
    advertise = models.ForeignKey(Advertise, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, null=False, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, null=True, on_delete=models.CASCADE)
    times = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
