from django.conf.urls import url
from notify.views.subscription import (
    SubscriptionSearch, SubscribeSLN, SubscriptionProtocol)
from notify.views.channel import (
    ChannelDetails, ChannelUnsubscribe, ChannelSearch)
from notify.views.endpoint import (
    EndpointView, ResendSMSConfirmationView, ToSConfirmation)
from notify.views.admin import (
    EndpointSearchAdmin, ChannelSearchAdmin, UserSearchAdmin,
    SubscriptionSearchAdmin)
from notify.views.ui import (
    home_view, profile_view, find_view, tos_view, detail_view,
    unsubscribe_view, course_view, shib_redirect, admin)


urlpatterns = [
    url(r'^$', home_view),
    url(r'^login/$', shib_redirect),
    url(r'^profile/', profile_view),
    url(r'^find/', find_view),
    url(r'^tos/', tos_view),
    url(r'^class_details/(?P<channel_id>[^/]+)', detail_view),
    url(r'^subscribe/', SubscribeSLN().run),
    url(r'^unsubscribe/(?P<channel_id>[^/]+)', unsubscribe_view),
    url(r'^uiapi/unsubscribe/', ChannelUnsubscribe().run),
    url(r'^uiapi/channel_details/(?P<channel_id>[^/]+)', ChannelDetails().run),
    url(r'^uiapi/subscription/?$', SubscriptionSearch().run),
    url(r'^uiapi/subscription_protocol/?$', SubscriptionProtocol().run),
    url(r'^uiapi/profile/(?P<user>[^/]+)', EndpointView().run),
    url(r'^uiapi/tos/(?P<user>[^/]+)', ToSConfirmation().run),
    url(r'^uiapi/resend_sms_confirmation/', ResendSMSConfirmationView().run),
    url(r'^uiapi/channel_search/', ChannelSearch().run),
    url(r'^admin/endpoint_search/', EndpointSearchAdmin().run),
    url(r'^admin/channel_search/', ChannelSearchAdmin().run),
    url(r'^admin/user_search/', UserSearchAdmin().run),
    url(r'^admin/subscription_search/', SubscriptionSearchAdmin().run),
    url(r'^admin/?$', admin),
    url(r'^course/(?P<year>\d{4})/(?P<quarter>\w+)/(?P<sln>\d+)/',
        course_view),
]
