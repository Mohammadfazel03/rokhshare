from rest_framework.fields import IntegerField, CharField
from rest_framework.serializers import Serializer, ModelSerializer

from advertise.models import Advertise
from movie.serializers import MediaFileSerializer


class DashboardAdvertiseSerializer(ModelSerializer):
    must_played = IntegerField(source='number_repeated')
    view_number = IntegerField()

    class Meta:
        model = Advertise
        fields = ('created_at', 'title', 'must_played', 'view_number')


class CreateAdvertiseSerializer(ModelSerializer):
    class Meta:
        model = Advertise
        fields = "__all__"


class AdvertiseSerializer(ModelSerializer):
    file = MediaFileSerializer(read_only=True)
    must_played = IntegerField(source='number_repeated')
    view_number = IntegerField()

    class Meta:
        model = Advertise
        fields = ('id', 'created_at', 'title', 'must_played', 'time', 'file', 'view_number')
