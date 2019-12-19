from django.urls import re_path
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
    HomeView, ProfileView, FindView, CourseView, DetailView, ConfirmView,
    UnsubscribeView, ToSView, AdminView)


urlpatterns = [
    re_path(r'^$', HomeView.as_view(), name='home'),
    re_path(r'^profile/', ProfileView.as_view()),
    re_path(r'^find/', FindView.as_view()),
    re_path(r'^tos/', ToSView.as_view(), name='tos'),
    re_path(r'^class_details/(?P<channel_id>[^/]+)', DetailView.as_view()),
    re_path(r'^subscribe/', SubscribeSLN.as_view()),
    re_path(r'^unsubscribe/(?P<channel_id>[^/]+)', UnsubscribeView.as_view()),
    re_path(r'^uiapi/unsubscribe/', ChannelUnsubscribe.as_view()),
    re_path(r'^uiapi/channel_details/(?P<channel_id>[^/]+)',
            ChannelDetails.as_view()),
    re_path(r'^uiapi/subscription/?$', SubscriptionSearch.as_view()),
    re_path(r'^uiapi/subscription_protocol/?$',
            SubscriptionProtocol.as_view()),
    re_path(r'^uiapi/profile/?$', EndpointView.as_view()),
    re_path(r'^uiapi/tos/?$', ToSConfirmation.as_view()),
    re_path(r'^uiapi/resend_sms_confirmation/',
            ResendSMSConfirmationView.as_view()),
    re_path(r'^uiapi/channel_search/', ChannelSearch.as_view()),
    re_path(r'^admin/endpoint_search/', EndpointSearchAdmin.as_view()),
    re_path(r'^admin/channel_search/', ChannelSearchAdmin.as_view()),
    re_path(r'^admin/user_search/', UserSearchAdmin.as_view()),
    re_path(r'^admin/subscription_search/', SubscriptionSearchAdmin.as_view()),
    re_path(r'^admin/?$', AdminView.as_view()),
    re_path(r'^course/(?P<year>\d{4})/(?P<quarter>\w+)/(?P<sln>\d+)/',
            CourseView.as_view()),
]
