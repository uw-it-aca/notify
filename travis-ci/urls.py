from django.conf.urls import include, re_path


urlpatterns = [
    re_path(r'^', include('notify.urls')),
    re_path(r'^saml/', include('uw_saml.urls')),
    re_path(r'^support/?', include('userservice.urls')),
    re_path(r'^persistent_message/', include('persistent_message.urls')),
]
