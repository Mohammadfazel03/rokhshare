from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import AuthViewSet, GenreViewSet, CountryViewSet, ArtistViewSet, MovieViewSet

url = DefaultRouter()
url.register('auth', AuthViewSet, basename='auth')
url.register('genre', GenreViewSet, basename='genre')
url.register('country', CountryViewSet, basename='country')
url.register('artist', ArtistViewSet, basename='artist')
url.register('movie', MovieViewSet, basename='movie')

urlpatterns = [
                  path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
              ] + url.get_urls()
