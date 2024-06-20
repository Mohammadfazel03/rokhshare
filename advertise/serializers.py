from rest_framework.fields import IntegerField, CharField
from rest_framework.serializers import Serializer, ModelSerializer

from advertise.models import Advertise


class DashboardAdvertiseSerializer(ModelSerializer):
    must_played = IntegerField(source='number_repeated')
    view_number = CharField()

    class Meta:
        model = Advertise
        fields = ('created_at', 'title', 'must_played', 'view_number')
