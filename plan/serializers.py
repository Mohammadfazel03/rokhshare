from rest_framework import serializers

from plan.models import Plan


class DashboardPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        exclude = ("description")
