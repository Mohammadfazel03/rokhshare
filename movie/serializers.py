from rest_framework.serializers import *

from movie.models import Genre, Country


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class CountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"

