from .base_urls import *
from django.urls import include, re_path


urlpatterns += [
    re_path(r'^', include('notify.urls')),
    re_path(r'^', include('django_prometheus.urls')),
    re_path(r'^support/?', include('userservice.urls')),
    re_path(r'^restclients/', include('rc_django.urls')),
    re_path(r'^persistent_message/', include('persistent_message.urls')),
]
