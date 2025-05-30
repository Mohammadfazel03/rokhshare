from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from plan.models import Plan, Payment, Subscription


class DashboardPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        exclude = ("description",)


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class UpdatePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["is_enable"]


class PaymentSerializer(serializers.ModelSerializer):
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(is_enable=True),
                                              many=False, allow_null=False,
                                              write_only=True)

    class Meta:
        model = Payment
        exclude = ['user', 'date', 'is_successful']

    def create(self, validated_data):
        plan = validated_data.pop('plan')
        with transaction.atomic():
            time = timezone.now() + timedelta(days=plan.days)
            payment = Payment.objects.create(**validated_data, is_successful=True,
                                             user=self.context.get('request').user)
            subscription = Subscription.objects.create(
                user=self.context.get('request').user,
                payment=payment,
                plan=plan,
                end_date=time,
                title_plan=plan.title,
                description_plan=plan.description,
                days_plan=plan.days,
                price_plan=plan.price
            )

        return payment, subscription


class PaymentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        exclude = ['user']


class SubscriptionSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer()

    class Meta:
        model = Subscription
        exclude = ['user', 'plan']
