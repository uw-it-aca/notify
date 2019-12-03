from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import utc
from uw_nws import NWS
from uw_nws.exceptions import InvalidUUID
from restclients_core.exceptions import DataFailureException
from notify.views.rest_dispatch import RESTDispatch
from notify.utilities import (
    get_channel_details_by_channel_id, get_course_details_by_channel,
    get_verified_endpoints_by_protocol)
from userservice.user import UserService
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


def valid_channel_id(channel_id):
    if channel_id in getattr(settings, 'INVALID_UUIDS', []):
        raise InvalidUUID(channel_id)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChannelDetails(RESTDispatch):
    def get(self, request, *args, **kwargs):
        channel_id = kwargs.get('channel_id')
        try:
            valid_channel_id(channel_id)
            data = get_channel_details_by_channel_id(channel_id)
            data['channel_id'] = channel_id
        except DataFailureException as ex:
            return self.error_response(
                status=404, message="Failed to retrieve channel details")
        except InvalidUUID:
            return self.error_response(
                status=400, message="Invalid channel_id")
        return self.json_response(data)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChannelUnsubscribe(RESTDispatch):
    def post(self, request, *args, **kwargs):
        """Unsubscribe from channel"""
        request_data = json.loads(request.body)
        channel_id = request_data['ChannelID']
        netid = UserService().get_user()

        subs = []
        nws = NWS(actas_user=UserService().get_original_user())
        try:
            valid_channel_id(channel_id)
            subs = nws.get_subscriptions_by_channel_id_and_subscriber_id(
                channel_id, netid)
        except DataFailureException as ex:
            return self.error_response(
                status=404, message="Unable to retrieve subscriptions")
        except InvalidUUID:
            return self.error_response(
                status=400, message="Invalid ChannelID")

        if len(subs) == 0:
            return self.error_response(
                status=404, message="User has no subscriptions to channel")

        failed_deletions = []
        for subscription in subs:
            subscription_id = subscription.subscription_id
            try:
                nws.delete_subscription(subscription_id)
                logger.info("DELETE subscription {}".format(subscription_id))
            except DataFailureException as ex:
                logger.warning(ex.msg)
                failed_deletions.append(subscription_id)

        n_failed = len(failed_deletions)
        if n_failed > 0:
            return self.error_response(
                status=500,
                message="Failed to unsubscribe from {} subscriptions".format(
                    n_failed))

        return self.json_response({'message': 'Unsubscription successful'})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class ChannelSearch(RESTDispatch):
    def get(self, request, *args, **kwargs):
        sln = request.GET.get('sln', None)
        quarter = request.GET.get('quarter', None)
        year = request.GET.get('year', None)

        subscriber_id = UserService().get_user()
        if subscriber_id is None:
            return self.error_response(
                status=401, message="No user is logged in")

        channel_type = 'uw_student_courseavailable'
        channels = None
        channel_id = None
        quarter_name = ' '.join([quarter, year])
        msg_no_class_by_sln = 'No class found with SLN {} for {}'.format(
            sln, quarter_name)
        msg_expired_channel = 'The section SLN {} for {} has expired.'.format(
            sln, quarter_name)

        nws = NWS()
        try:
            channels = nws.get_channels_by_sln_year_quarter(
                channel_type, sln, year, quarter)
        except DataFailureException as ex:
            return self.error_response(status=404, message=msg_no_class_by_sln)

        if channels is not None and len(channels) > 0:
            channel = channels[0]
        else:
            return self.error_response(status=404, message=msg_no_class_by_sln)

        channel_expires = channel.expires
        now = datetime.utcnow().replace(tzinfo=utc)
        if channel_expires and now >= channel_expires:
            return self.error_response(status=404, message=msg_expired_channel)

        channel_id = channel.channel_id
        data = get_course_details_by_channel(channel)
        data['ChannelID'] = channel_id
        data['SLN'] = sln

        if 'add_code_required' in data and data['add_code_required']:
            msg_add_code = (
                "No notifications are available for this course. {} (SLN: {}) "
                "requires an Add Code for registration. Please consult the "
                "Time Schedule about where to obtain the Add Code required to "
                "register for this course. ").format(
                    data['course_abbr'], data['section_sln'])
            return self.error_response(status=404, message=msg_add_code)

        if 'faculty_code_required' in data and data['faculty_code_required']:
            msg_faculty_code = (
                "No notifications are available for this course. {} (SLN: {}) "
                "is an independent study course. Please consult the Time "
                "Schedule about where to obtain the Faculty Code required to "
                "register for this course. ").format(
                    data['course_abbr'], data['section_sln'])
            return self.error_response(status=404, message=msg_faculty_code)

        # check if user is already subscribed
        subs = []
        try:
            subs = nws.get_subscriptions_by_channel_id_and_subscriber_id(
                channel_id, subscriber_id)
        except DataFailureException as ex:
            pass

        verified_endpoints = get_verified_endpoints_by_protocol(subscriber_id)

        for protocol in ['email', 'sms']:
            if protocol not in verified_endpoints:
                data['class_unverified_' + protocol] = ' disabled'

        for subscription in subs:
            protocol = subscription.endpoint.protocol.lower()
            data['HasSubscription' + protocol] = True

        return self.json_response(data)
