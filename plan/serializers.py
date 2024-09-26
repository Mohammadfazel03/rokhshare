from rest_framework import serializers

from plan.models import Plan


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
