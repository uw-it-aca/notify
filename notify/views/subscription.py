from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.timezone import utc
from uw_nws import NWS
from uw_nws.models import Subscription
from restclients_core.exceptions import DataFailureException
from notify.utilities import (
    get_course_details_by_channel, get_person, get_quarter_index)
from notify.views.rest_dispatch import RESTDispatch
from userservice.user import UserService
from datetime import datetime
from operator import attrgetter
import logging
import json

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class SubscriptionSearch(RESTDispatch):
    def get(self, request, *args, **kwargs):
        subscriber_id = UserService().get_user()
        if subscriber_id is None:
            return self.error_response(
                status=400, message="No subscriber ID provided")

        try:
            person = get_person(subscriber_id)
        except DataFailureException as ex:
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        nws = NWS()
        try:
            subscriptions = nws.get_subscriptions_by_subscriber_id(
                subscriber_id, max_results=100)
        except DataFailureException as ex:
            logger.warning(ex.msg)
            return self.error_response(
                status=500, message="Search error: %s" % ex.msg)

        data = {"TotalCount": len(subscriptions), "Subscriptions": []}

        channel_ids = {}
        utcnow = datetime.utcnow().replace(tzinfo=utc)
        channels_by_reg_period = {}
        for subscription in subscriptions:
            # a channel can have more than one subscription,
            # keep track of known channels
            channel_id = subscription.channel.channel_id
            if channel_id in channel_ids:
                continue

            try:
                channel = nws.get_channel_by_channel_id(channel_id)

                if (channel.expires and channel.expires <= utcnow):
                    continue

                channel_details = get_course_details_by_channel(channel)

            except DataFailureException as ex:
                continue

            # for reg_period grouping on subscriptions list
            (year, quarter, curr_abbr,
                course_no, section_id) = channel.surrogate_id.split(",")
            reg_period_idx = "{0}{1}".format(year, get_quarter_index(quarter))
            if reg_period_idx not in channels_by_reg_period:
                channels_by_reg_period[reg_period_idx] = {
                    "RegistrationPeriod": "{0} {1}".format(
                        quarter.capitalize(), year),
                    "Channels": []}

            current_enrollment = channel_details.get('current_enrollment',
                                                     0)
            total_seats = channel_details.get('total_seats', 0)
            filled_state = 'full' if (
                current_enrollment >= total_seats) else 'open'

            channels_by_reg_period[reg_period_idx]["Channels"].append({
                "ChannelID": channel.channel_id,
                "SurrogateID": channel.surrogate_id,
                "Name": channel.name,
                "course_abbr": channel_details.get(
                    'course_abbr', channel.name),
                "Description": channel.description,
                "section_sln": channel_details.get(
                    'section_sln', '(unknown)'),
                "current_enrollment": current_enrollment,
                "total_seats": total_seats,
                "filled_state": filled_state
            })
            channel_ids[channel.channel_id] = True

            data["Subscriptions"].append({
                "Subscription": {
                    "SubscriptionID": subscription.subscription_id,
                    "Channel": {
                        "ChannelID": subscription.channel.channel_id
                    },
                    "Endpoint": {
                        "EndpointID": subscription.endpoint.endpoint_id,
                        "Protocol": subscription.endpoint.protocol
                    }
                }
            })

        data["MissingEndpoints"] = ["sms", "email"]
        data["Endpoints"] = {}
        for endpoint in person.endpoints:
            protocol = endpoint.protocol.lower()
            if protocol in data["MissingEndpoints"]:
                data["MissingEndpoints"].remove(protocol)
            data["Endpoints"][protocol] = {
                "EndpointId": endpoint.endpoint_id,
                "Status": endpoint.status,
                "Active": endpoint.active,
                "Protocol": protocol
            }

        data["RegistrationPeriods"] = []
        for regperiod in sorted(channels_by_reg_period, reverse=True):
            channel_data = channels_by_reg_period[regperiod]
            data["RegistrationPeriods"].append({
                "RegistrationPeriod": channel_data["RegistrationPeriod"],
                "Channels": sorted(channel_data["Channels"],
                                   key=lambda course: course["course_abbr"])
            })

        return self.json_response(data)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class SubscribeSLN(RESTDispatch):
    def post(self, request, *args, **kwargs):
        sln = request.POST.get('sln')
        channel_id = request.POST.get('channel_id')
        protocols = request.POST.getlist('protocol')
        subscriber_id = UserService().get_user()

        data = {
            "subscriber_id": subscriber_id,
            "channel_id": channel_id,
            "sln": sln,
            "protocols": protocols
        }

        nws = NWS(UserService().get_acting_user())
        try:
            channel = nws.get_channel_by_channel_id(channel_id)
        except DataFailureException as ex:
            msg = 'Error retrieving channel {0}'.format(channel_id)
            return self.error_response(status=404, message=msg)

        try:
            person = get_person(subscriber_id)
        except DataFailureException as ex:
            msg = 'Error retrieving Person ' + subscriber_id
            return self.error_response(status=404, message=msg)

        endpoints_by_protocol = {}
        for endpoint in person.endpoints:
            endpoints_by_protocol[endpoint.protocol.lower()] = endpoint

        if not endpoints_by_protocol:
            return self.error_response(status=404,
                                       message='Person has no endpoints')

        for protocol in protocols:
            subscription = Subscription()
            subscription.channel = channel
            if protocol.lower() in endpoints_by_protocol:
                subscription.endpoint = endpoints_by_protocol[protocol.lower()]
            else:
                msg = "No endpoint of type: %s" % protocol.lower()
                return self.error_response(status=404, message=msg)
            subscription.subscriber_id = subscriber_id
            subscription.owner_id = subscriber_id

            try:
                status = nws.create_subscription(subscription)
            except DataFailureException as ex:
                if channel.expires <= datetime.utcnow().replace(tzinfo=utc):
                    content = {
                        'sln': channel.tags.get('sln'),
                        'year': channel.tags.get('year'),
                        'quarter': channel.tags.get('quarter').capitalize()}
                    return self.error_response(
                        status=403, message="Channel expired", content=content)
                else:
                    logger.warning(ex.msg)
                    return self.error_response(
                        status=500,
                        message="Error subscribing to channel: %s" % ex.msg)

        return self.json_response(status=201)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionProtocol(RESTDispatch):
    """Enables or disables a subscription protocol (e.g. Email or Mobile)
    """
    def _echo_request_data(self, request, method):
        try:
            request_data = json.loads(request.body)
            request_data['method'] = method
            request_data['subscriber_id'] = request.META['REMOTE_USER']
            return self.json_response(request_data)
        except Exception as ex:
            logger.exception(ex)
            return self.error_response(status=304)

    def put(self, request, *args, **kwargs):
        request_data = json.loads(request.body)
        subscriber_id = UserService().get_user()
        protocol = request_data['Protocol']
        channel_id = request_data['ChannelID']

        nws = NWS(UserService().get_acting_user())
        try:
            channel = nws.get_channel_by_channel_id(channel_id)
        except Exception as ex:
            logger.exception(ex)
            msg = 'Error retrieving channel {0}'.format(channel_id)
            return self.error_response(status=404, message=msg)

        # ensure user's endpoint exists
        endpoints = []
        msg = 'Failed to retrieve {0} endpoint for {1}'.format(
            protocol, subscriber_id)

        try:
            endpoints = nws.get_endpoints_by_subscriber_id(subscriber_id)
        except DataFailureException as ex:
            return self.error_response(status=404, message=msg)

        if not len(endpoints):
            return self.error_response(status=404, message=msg)

        endpoint = None
        for ep in endpoints:
            if ep.protocol.lower() == protocol.lower():
                endpoint = ep

        if endpoint is None:
            return self.error_response(status=404, message=msg)

        subscription = Subscription()
        subscription.channel = channel
        subscription.endpoint = endpoint
        subscription.protocol = protocol
        subscription.user = subscriber_id
        subscription.owner = subscriber_id

        status = None
        try:
            status = nws.create_new_subscription(subscription)
        except DataFailureException as ex:
            logger.warning(ex.msg)
            return self.error_response(
                status=500, message='Subscription creation failed')

        return self.json_response(
            {'status': status, 'message': 'Subscription successful'})

    def delete(self, request, *args, **kwargs):
        request_data = json.loads(request.body)
        protocol = request_data['Protocol']
        channel_id = request_data['ChannelID']
        endpoint_id = request_data['EndpointID']
        user = UserService().get_user()

        nws = NWS(UserService().get_acting_user())
        # confirm endpoint belongs to subscriber
        try:
            endpoint = nws.get_endpoint_by_endpoint_id(endpoint_id)
        except DataFailureException as ex:
            msg = 'Endpoint "{0}" not found'.format(endpoint_id)
            return self.error_response(status=404, message=msg)

        if user != endpoint.user:
            msg = '"{0}" does not own endpoint "{1} {2}"'.format(
                  user, protocol, endpoint_id)
            return self.error_response(status=403, message=msg)

        # confirm subscription exists
        try:
            subscription = nws.get_subscription_by_channel_id_and_endpoint_id(
                channel_id=channel_id, endpoint_id=endpoint_id)
        except DataFailureException as ex:
            msg = '{0} endpoint "{1}" not subscribed to channel "{2}"'.format(
                  protocol, endpoint_id, channel_id)
            return self.error_response(status=404, message=msg)

        subscription_id = subscription.subscription_id
        try:
            status = nws.delete_subscription(subscription_id)
        except self.error_response as ex:
            msg = 'Failed to delete subscription {0}'.format(subscription_id)
            return self.error_response(status=500, message=msg)

        return self.json_response(
            {'status': status, 'message': 'Subscription deleted'})

    def post(self, request, *args, **kwargs):
        channel_id = request.POST.get('channel_id')
        protocols = request.POST.getlist('protocol')
        subscriber_id = UserService().get_user()
        status = 500
        subscriptions = []
        subscribed_protocols = []
        n_unsubscribed = 0

        nws = NWS(UserService().get_acting_user())
        try:
            channel = nws.get_channel_by_channel_id(channel_id)
        except DataFailureException as ex:
            msg = 'Error retrieving channel {0}'.format(channel_id)
            return self.error_response(status=404, message=msg)

        try:
            subs = nws.get_subscriptions_by_channel_id_and_subscriber_id(
                channel_id, subscriber_id)
        except DataFailureException as ex:
            pass

        if len(subs):
            for subscription in subs:
                sub_protocol = subscription.endpoint.protocol.lower()
                if sub_protocol not in protocols:
                    # unsubscribe
                    try:
                        status = nws.delete_subscription(
                            subscription.subscription_id)
                        n_unsubscribed += 1
                    except DataFailureException as ex:
                        pass
                else:
                    # already subscribed
                    protocols.remove(sub_protocol)
                    subscribed_protocols.append(sub_protocol)

        if len(protocols) == 0:
            if (n_unsubscribed > 0):
                msg = 'Unsubscription successful'
            else:
                msg = 'No changes'
            return self.json_response({
                'status': 200,
                'message': msg,
                'subscribed_protocols': subscribed_protocols
            })

        # subscribe remaining protocolos
        try:
            person = get_person(subscriber_id)
        except DataFailureException as ex:
            msg = 'Error retrieving person {0}'.format(subscriber_id)
            return self.error_response(status=404, message=msg)

        for ep in person.endpoints:
            if ep.protocol.lower() in protocols:
                subscription = Subscription()
                subscription.channel = channel
                subscription.endpoint = ep
                subscription.protocol = ep.protocol
                subscription.user = subscriber_id
                subscription.owner = subscriber_id

                try:
                    status = nws.create_new_subscription(subscription)
                    subscribed_protocols.append(ep.protocol.lower())
                except DataFailureException as ex:
                    pass

        return self.json_response({
            'status': status,
            'message': 'Subscription update successful',
            'subscribed_protocols': subscribed_protocols
        })
