from rest_framework.serializers import *

from movie.models import Genre


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"

