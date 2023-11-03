from rest_framework.routers import DefaultRouter

from api.views import AuthViewSet

url = DefaultRouter()
url.register('auth', AuthViewSet, basename='auth')

urlpatterns = url.get_urls()