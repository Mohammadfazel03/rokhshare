from moviepy import VideoFileClip
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, CharField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import Serializer, ModelSerializer

from advertise.models import Advertise
from movie.models import Media, Episode, MediaFile
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


    def validate(self, attrs):
        time = attrs.pop('time', 0)
        if time == 0:
            time = VideoFileClip(attrs.get('file').file.path).duration
        attrs['time'] = time
        return attrs


class AdvertiseSerializer(ModelSerializer):
    file = MediaFileSerializer(read_only=True)
    must_played = IntegerField(source='number_repeated')
    view_number = IntegerField()

    class Meta:
        model = Advertise
        fields = ('id', 'created_at', 'title', 'must_played', 'time', 'file', 'view_number')


class AdvertiseSeenSerializer(Serializer):
    media = PrimaryKeyRelatedField(write_only=True, required=True, queryset=Media.objects.filter())
    episode = PrimaryKeyRelatedField(write_only=True, allow_null=True, required=False,
                                     queryset=Episode.objects.filter())

    def validate(self, attrs):
        if attrs['episode']:
            try:
                Episode.objects.get(season__series__media=attrs['media'], pk=attrs['episode'].pk)
            except Episode.DoesNotExist:
                raise ValidationError()

        return attrs


class AdvertiseMediaFileSerializer(ModelSerializer):
    file = SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = ['file', 'id', 'mimetype', 'thumbnail']

    def get_file(self, instance):
        url = f'/api/v1/stream/{instance.pk}/file/'
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url


class PlayAdvertiseSerializer(ModelSerializer):
    file = AdvertiseMediaFileSerializer(read_only=True)

    class Meta:
        model = Advertise
        fields = ('id', 'title', 'file')
