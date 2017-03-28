from django.conf.urls import patterns, url
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
    url(r'^$', 'notify.views.ui.home_view'),
    url(r'^profile/', 'notify.views.ui.profile_view'),
    url(r'^find/', 'notify.views.ui.find_view'),
    url(r'^tos/', 'notify.views.ui.tos_view'),
    url(r'^class_details/(?P<channel_id>[^/]+)',
        'notify.views.ui.detail_view'),
    url(r'^subscribe/', SubscribeSLN().run),
    url(r'^unsubscribe/(?P<channel_id>[^/]+)', 'notify.views.ui.tos_view'),
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
        'notify.views.ui.course_view'),
)
