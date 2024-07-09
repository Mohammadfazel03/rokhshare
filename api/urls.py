from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import AuthViewSet, GenreViewSet, CountryViewSet, ArtistViewSet, MovieViewSet, SeriesViewSet, \
    SeasonViewSet, EpisodeViewSet, MediaGalleryViewSet, SliderViewSet, CollectionViewSet, CommentViewSet, RatingViewSet, \
    DashboardViewSet, AdminMediaViewSet

url = DefaultRouter()
url.register('auth', AuthViewSet, basename='auth')
url.register('genre', GenreViewSet, basename='genre')
url.register('country', CountryViewSet, basename='country')
url.register('artist', ArtistViewSet, basename='artist')
url.register('movie', MovieViewSet, basename='movie')
url.register('serial/season/episode', EpisodeViewSet, basename='serial-season-episode')
url.register('serial/season', SeasonViewSet, basename='serial-season')
url.register('serial', SeriesViewSet, basename='serial')
url.register('media/gallery', MediaGalleryViewSet, basename='media-gallery')
url.register('slider', SliderViewSet, basename='slider')
url.register('collection', CollectionViewSet, basename='collection')
url.register('comment', CommentViewSet, basename='comment')
url.register('rating', RatingViewSet, basename='rating')
url.register('dashboard', DashboardViewSet, basename='dashboard')
url.register('admin/media', AdminMediaViewSet, basename='admin-media')

urlpatterns = [
                  path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
              ] + url.get_urls()
