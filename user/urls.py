from django.urls import path, re_path

from user import views

urlpatterns = [
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z_\-]+)/$',
            views.activate, name='user-active'),
]
