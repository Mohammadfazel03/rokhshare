from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from plan.models import Subscription


# Create your models here.

class User(AbstractUser):

    @property
    def is_subscriber(self):
        if self.is_anonymous or not self.is_authenticated:
            return False
        now = timezone.now()
        return Subscription.objects.filter(user=self, end_date__gt=now).exists()


class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, null=False)
    expire_date = models.DateTimeField()
