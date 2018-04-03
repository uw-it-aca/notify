from django.conf import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from uw_saml.decorators import group_required
from uw_nws import NWS
from uw_pws import PWS
from restclients_core.exceptions import (
    DataFailureException, InvalidRegID, InvalidNetID)
from uw_nws.exceptions import InvalidUUID
from notify.views.rest_dispatch import RESTDispatch
from notify.utilities import netid_from_eppn
from userservice.user import UserService
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote


@method_decorator(group_required(settings.USERSERVICE_ADMIN_GROUP),
                                 name='dispatch')
@method_decorator(never_cache, name='dispatch')
class EndpointSearchAdmin(RESTDispatch):
    def get(self, request, *args, **kwargs):
        endpoint_address = request.GET.get('endpoint_address', None)
        endpoint_id = request.GET.get('endpoint_id', None)

        try:
            if endpoint_id is not None:
                endpoint = NWS().get_endpoint_by_endpoint_id(endpoint_id)
            elif endpoint_address is not None:
                endpoint = NWS().get_endpoint_by_address(
                    quote(endpoint_address))
            else:
                return self.error_response(
                    status=400, message="No search term provided")
        except DataFailureException as ex:
            return self.error_response(
                status=404, message="No endpoints found")

        return self.json_response(endpoint.json_data())

    def delete(self, request, *args, **kwargs):
        endpoint_id = request.GET.get('endpoint_id', None)

        if endpoint_id is not None:
            nws = NWS(actas_user=UserService().get_original_user())
            try:
                endpoint = nws.delete_endpoint(endpoint_id)
            except DataFailureException as ex:
                if ex.status == 410:
                    return self.json_response()
                return self.error_response(
                    status=404, message="No endpoints found")
        else:
            return self.error_response(
                status=404, message="No endpoint found for that ID")

        return self.json_response({"message": "Endpoint deleted"})


@method_decorator(group_required(settings.USERSERVICE_ADMIN_GROUP),
                                 name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChannelSearchAdmin(RESTDispatch):
    def get(self, request, *args, **kwargs):
        channel_id = request.GET.get('channel_id', '').strip()
        channel_year = request.GET.get('channel_year', '').strip()
        channel_quarter = request.GET.get('channel_quarter', '').strip()
        channel_sln = request.GET.get('channel_sln', '').strip()

        try:
            nws = NWS()
            if len(channel_id):
                channel = nws.get_channel_by_channel_id(channel_id)
            elif (len(channel_year) and len(channel_sln) and
                    len(channel_quarter)):
                channel_type = "uw_student_courseavailable"
                search_result = nws.get_channels_by_sln_year_quarter(
                    channel_type, channel_sln, channel_year, channel_quarter)
                if not len(search_result):
                    return self.error_response(
                        status=400, message="No channels found")
                channel = search_result[0]
            else:
                return self.error_response(
                    status=400, message="Invalid search")

            return self.json_response(channel.json_data())

        except DataFailureException:
            return self.error_response(status=404, message="No channels found")
        except InvalidUUID:
            return self.error_response(
                status=400, message="Invalid channel ID")


@method_decorator(group_required(settings.USERSERVICE_ADMIN_GROUP),
                                 name='dispatch')
@method_decorator(never_cache, name='dispatch')
class UserSearchAdmin(RESTDispatch):
    def get(self, request, *args, **kwargs):
        regid = request.GET.get('regid', '').strip()
        netid = request.GET.get('netid', '').strip()

        if not len(netid) and not len(regid):
            return self.error_response(status=400, message="Missing input")

        # search by netid
        if len(netid) > 0:
            try:
                pws_person = PWS().get_person_by_netid(netid)
                regid = pws_person.uwregid
            except DataFailureException as ex:
                return self.error_response(
                    status=400, message="NETID does not exist")
            except InvalidNetID as ex:
                return self.error_response(
                    status=400, message="Invalid NETID")

        # search by regid
        if len(regid) > 0:
            try:
                person = NWS().get_person_by_uwregid(regid)
            except DataFailureException as ex:
                return self.error_response(
                    status=400,
                    message="User has not signed up to use Notify.UW")
            except InvalidRegID as ex:
                return self.error_response(
                    status=400, message="Invalid REGID")

        return self.json_response(person.json_data())


@method_decorator(group_required(settings.USERSERVICE_ADMIN_GROUP),
                                 name='dispatch')
@method_decorator(never_cache, name='dispatch')
class SubscriptionSearchAdmin(RESTDispatch):
    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('person_id')

        response_json = {'Subscriptions': []}
        try:
            subscriptions = NWS().get_subscriptions_by_subscriber_id(
                user_id, '1000')
            for subscription in subscriptions:
                response_json['Subscriptions'].append(subscription.json_data())
        except DataFailureException as ex:
            return self.error_response(
                status=400, message=("User does not exist or has not signed "
                                     "up to use Notify.UW"))

        return self.json_response(response_json)
