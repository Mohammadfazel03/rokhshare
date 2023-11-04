from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import AuthViewSet

url = DefaultRouter()
url.register('auth', AuthViewSet, basename='auth')

urlpatterns = [
                  path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
              ] + url.get_urls()
