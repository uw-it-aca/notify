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
import json


class ChannelDetails(RESTDispatch):
    def GET(self, request, channel_id):
        try:
            data = get_channel_details_by_channel_id(channel_id)
            data['channel_id'] = channel_id
        except DataFailureException as ex:
            message = 'Failed to retrieve channel details'
            return self.error_response(status=404, message=message)
        except InvalidUUID:
            message = 'Failed to retrieve channel details'
            return self.error_response(status=400, message=message)
        return self.json_response(data)


class ChannelUnsubscribe(RESTDispatch):
    def POST(self, request):
        """Unsubscribe from channel"""
        request_data = json.loads(request.body)
        channel_id = request_data['ChannelID']
        user_service = UserService()
        netid = user_service.get_user()

        subs = []
        nws = NWS(user_service.get_acting_user())
        try:
            subs = nws.get_subscriptions_by_channel_id_and_subscriber_id(
                channel_id, netid)
        except DataFailureException as ex:
            return self.error_response(
                status=404, message="unable to retrieve subscriptions")

        if len(subs) == 0:
            return self.error_response(
                status=404, message="User has no subscriptions to channel")

        failed_deletions = []
        for subscription in subs:
            subscription_id = subscription.subscription_id
            try:
                nws.delete_subscription(subscription_id)
            except DataFailureException:
                failed_deletions.append(subscription_id)

        n_failed = len(failed_deletions)
        if n_failed > 0:
            return self.error_response(
                status=500,
                message="Failed to unsubscribe from %s subscriptions" % (
                    n_failed))

        return self.json_response({'message': 'Unsubscription successful'})


@csrf_exempt
class ChannelSearch(RESTDispatch):
    def GET(self, request):
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
        msg_no_class_by_sln = 'No class found with SLN %s for %s %s' % (
            sln, quarter, year)
        msg_expired_channel = 'The section SLN %s for %s %s has expired.' % (
            sln, quarter, year)

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
                "No notifications are available for this course. %s (SLN: %s) "
                "requires an Add Code for registration. Please consult the "
                "Time Schedule about where to obtain the Add Code required to "
                "register for this course. " % (
                    data['course_abbr'], data['section_sln']))
            return self.error_response(status=404, message=msg_add_code)

        if 'faculty_code_required' in data and data['faculty_code_required']:
            msg_faculty_code = (
                "No notifications are available for this course. %s (SLN: %s) "
                "is an independent study course. Please consult the Time "
                "Schedule about where to obtain the Faculty Code required to "
                "register for this course. " % (
                    data['course_abbr'], data['section_sln']))
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
