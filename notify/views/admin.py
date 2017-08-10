from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from uw_nws import NWS
from uw_pws import PWS
from restclients_core.exceptions import (
    DataFailureException, InvalidRegID, InvalidNetID)
from uw_nws.exceptions import InvalidUUID
from notify.views.rest_dispatch import RESTDispatch
from notify.utilities import netid_from_eppn
from userservice.user import UserService
from authz_group import Group
from urllib import quote


class InvalidAdminException(Exception):
    def __str__(self):
        return "User is not authorized for administrator activity"


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AdminRESTDispatch(RESTDispatch):
    def user_is_admin(self):
        actual_user = UserService().get_original_user()
        group_id = getattr(settings, 'USERSERVICE_ADMIN_GROUP')
        if not Group().is_member_of_group(actual_user, group_id):
            raise InvalidAdminException()


class EndpointSearchAdmin(AdminRESTDispatch):
    def get(self, request, *args, **kwargs):
        endpoint_address = request.GET.get('endpoint_address', None)
        endpoint_id = request.GET.get('endpoint_id', None)

        try:
            self.user_is_admin()
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
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

        return self.json_response(endpoint.json_data())

    def delete(self, request, *args, **kwargs):
        endpoint_id = request.GET.get('endpoint_id', None)

        try:
            self.user_is_admin()
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

        if endpoint_id is not None:
            nws = NWS(UserService().get_acting_user())
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


class ChannelSearchAdmin(AdminRESTDispatch):
    def get(self, request, *args, **kwargs):
        channel_id = request.GET.get('channel_id', '').strip()
        channel_year = request.GET.get('channel_year', '').strip()
        channel_quarter = request.GET.get('channel_quarter', '').strip()
        channel_sln = request.GET.get('channel_sln', '').strip()

        try:
            self.user_is_admin()
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
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)


class UserSearchAdmin(AdminRESTDispatch):
    def get(self, request, *args, **kwargs):
        regid = request.GET.get('regid', '').strip()
        netid = request.GET.get('netid', '').strip()

        try:
            self.user_is_admin()
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

        if not len(netid) and not len(regid):
            return self.error_response(status=400, message="Missing input")

        # search by netid
        if len(netid) > 0:
            try:
                pws_person = PWS().get_person_by_netid(netid)
                regid = pws_person.uwregid
            except (DataFailureException, InvalidNetID) as ex:
                return self.error_response(
                    status=400, message="NETID does not exist")

        # search by regid
        if len(regid) > 0:
            try:
                person = NWS().get_person_by_uwregid(regid)
            except DataFailureException as ex:
                return self.error_response(
                    status=400,
                    message="User has not signed up to use Notify.UW")

        return self.json_response(person.json_data())


class SubscriptionSearchAdmin(AdminRESTDispatch):
    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('person_id')

        response_json = {'Subscriptions': []}
        try:
            self.user_is_admin()
            subscriptions = NWS().get_subscriptions_by_subscriber_id(
                user_id, '1000')
            for subscription in subscriptions:
                response_json['Subscriptions'].append(subscription.json_data())
        except DataFailureException as ex:
            return self.error_response(
                status=400, message=("User does not exist or has not signed "
                                     "up to use Notify.UW"))
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

        return self.json_response(response_json)
