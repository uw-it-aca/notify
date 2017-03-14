from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from notify.views.ui import (
    HomeView, ProfileView, FindView, DetailsView, ToSView)
from notify.views.ui import UnsubscribeView, CourseView
from notify.views.subscription import (
    SubscriptionSearch, SubscribeSLN, SubscriptionProtocol)
from notify.views.channel import (
    ChannelDetails, ChannelUnsubscribe, ChannelSearch)
from notify.views.endpoint import (
    EndpointView, ResendSMSConfirmationView, ToSConfirmation)
from notify.views.admin import (
    EndpointSearchAdmin, ChannelSearchAdmin, UserSearchAdmin,
    SubscriptionSearchAdmin)


urlpatterns = patterns(
    '',
    url(r'^$', HomeView().run),
    url(r'^profile/', ProfileView().run),
    url(r'^find/', FindView().run),
    url(r'^tos/', ToSView().run),
    url(r'^class_details/(?P<channel_id>[^/]+)', DetailsView().run),
    url(r'^subscribe/', SubscribeSLN().run),
    url(r'^unsubscribe/(?P<channel_id>[^/]+)', UnsubscribeView().run),
    url(r'^uiapi/unsubscribe/', ChannelUnsubscribe().run),
    url(r'^uiapi/channel_details/(?P<channel_id>[^/]+)', ChannelDetails().run),
    url(r'^uiapi/subscription/?$', SubscriptionSearch().run),
    url(r'^uiapi/subscription_protocol/?$',
        csrf_exempt(SubscriptionProtocol().run)),
    url(r'^uiapi/profile/(?P<user>[^/]+)', EndpointView().run),
    url(r'^uiapi/tos/(?P<user>[^/]+)', ToSConfirmation().run),
    url(r'^uiapi/resend_sms_confirmation/', ResendSMSConfirmationView().run),
    url(r'^uiapi/channel_search/', csrf_exempt(ChannelSearch().run)),
    url(r'^accounts/login/$', 'ui.views.ui.shib_redirect'),
    url(r'^admin/endpoint_search/', EndpointSearchAdmin().run),
    url(r'^admin/channel_search/', ChannelSearchAdmin().run),
    url(r'^admin/user_search/', UserSearchAdmin().run),
    url(r'^admin/subscription_search/', SubscriptionSearchAdmin().run),
    url(r'^admin/?$', 'ui.views.ui.admin'),
    url(r'^course/(?P<year>\d{4})/(?P<quarter>\w+)/(?P<sln>\d+)/',
        CourseView().run),
)
