from django.db import models

from user.models import User


# Create your models here.
class Plan(models.Model):
    title = models.CharField(max_length=100, null=False)
    description = models.TextField(null=False)
    days = models.IntegerField(null=False)
    price = models.IntegerField(null=False)
    is_enable = models.BooleanField(null=False, blank=False, default=True)


class Payment(models.Model):
    date = models.DateTimeField(auto_created=True)
    price = models.IntegerField()
    tracking_code = models.IntegerField()
    receipt_number = models.IntegerField()
    is_successful = models.BooleanField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_created=True)
    end_date = models.DateTimeField()
    title_plan = models.CharField(max_length=100, null=False)
    description_plan = models.TextField(null=False)
    days_plan = models.IntegerField(null=False)
    price_plan = models.IntegerField(null=False)
