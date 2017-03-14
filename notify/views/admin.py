from restclients.nws import NWS
from restclients.pws import PWS
from restclients.exceptions import (
    DataFailureException, InvalidUUID, InvalidRegID, InvalidNetID)
from notify.views.rest_dispatch import RESTDispatch
from notify.utilities import netid_from_eppn
from userservice.user import UserService
from authz_group import Group
from django.conf import settings
from urllib import quote


class InvalidAdminException(Exception):
    def __str__(self):
        return "User is not authorized for administrator activity"


class AdminRESTDispatch(RESTDispatch):
    def user_is_admin(self):
        actual_user = UserService().get_original_user()
        group_id = getattr(settings, 'USERSERVICE_ADMIN_GROUP')
        if not Group().is_member_of_group(actual_user, group_id):
            raise InvalidAdminException()


class EndpointSearchAdmin(AdminRESTDispatch):
    def GET(self, request):
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

        owner = netidFromEPPN(endpoint.get_owner_net_id())
        return self.json_response({
            "id": endpoint.endpoint_id,
            "owner": owner,
            "address": endpoint.get_endpoint_address(),
            "modified": endpoint.last_modified.isoformat() if (
                endpoint.last_modified) else None,
            "status": endpoint.status,
            "active": endpoint.active})

    def DELETE(self, request):
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
    def GET(self, request):
        channel_id = request.GET['channel_id']
        channel_year = request.GET['channel_year']
        channel_quarter = request.GET['channel_quarter']
        channel_sln = request.GET['channel_sln']

        try:
            self.user_is_admin()
            nws = NWS()
            if len(channel_id) > 0:
                channel = nws.get_channel_by_channel_id(channel_id)
            elif len(channel_year) > 0 and len(channel_sln) > 0:
                search_result = nws.get_channels_by_sln_year_quarter(
                    "uw_student_courseavailable", channel_sln, channel_year,
                    channel_quarter)
                if len(search_result) < 1:
                    return self.error_response(
                        status=400, message="No channel found")
                channel = nws.get_channel_by_channel_id(
                    search_result.pop().channel_id)

            response_json = {
                "id": channel.channel_id,
                "type": channel.type,
                "name": channel.name,
                "created": channel.created.isoformat() if (
                    channel.created) else None,
                "expires": channel.expires.isoformat() if (
                    channel.expires) else None,
                "description": channel.description
            }
            tags = channel.get_tags()
            if tags is not None:
                for tag in tags:
                    response_json[tag.name] = tag.value

            return self.json_response(response_json)

        except DataFailureException:
            return self.error_response(status=404, message="No channels found")
        except InvalidUUID:
            return self.error_response(
                status=400, message="Invalid channel ID")
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)


class UserSearchAdmin(AdminRESTDispatch):
    def GET(self, request):
        regid = request.GET['regid']
        netid = request.GET['netid']

    try:
        self.user_is_admin()
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

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

        if person is None:
            return self.error_response(status=404, message="No person found")

        response_json = {
            'PersonID': person.person_id,
            'SurrogateID': person.surrogate_id,
            'Created': person.created.isoformat() if (
                person.created) else None,
            'LastModified': person.last_modified.isoformat() if (
                person.last_modified) else None,
            'ModifiedBy': person.modified_by
        }

        # Get person attributes
        attribs = person.get_attributes()
        if attribs is not None:
            attrib_dict = {}
            for attrib in attribs:
                attrib_dict[attrib.name] = attrib.value
            response_json['Attributes'] = attrib_dict

        # Get links to endpoint resources
        endpoints = person.get_endpoints()
        if endpoints is not None:
            endpoint_dict = {}
            for endpoint in endpoints:
                address = endpoint.get_endpoint_address()
                endpoint_dict[address] = endpoint.endpoint_id
            response_json["Endpoints"] = endpoint_dict

        return self.json_response(response_json)


class SubscriptionSearchAdmin(AdminRESTDispatch):
    def GET(self, request):
        user_id = request.GET['person_id']

        response_json = {'Subscriptions': []}
        try:
            self.user_is_admin()
            subscriptions = NWS().get_subscriptions_by_subscriber_id(
                user_id, '1000')
            for subscription in subscriptions:
                response_json['Subscriptions'].append({
                    "SubscriptionID": subscription.subscription_id,
                    "LastModified": subscription.last_modified.isoformat() if (
                        subscription.last_modified) else None,
                    "ChannelID": subscription.channel.channel_id,
                    "Name": subscription.channel.name,
                    "Expires": subscription.channel.expires.isoformat() if (
                        subscription.channel.expires) else None,
                    "EndpointID": subscription.endpoint.endpoint_id,
                    "EndpointAddress": (
                        subscription.endpoint.get_endpoint_address())
                })
        except DataFailureException as ex:
            return self.error_response(
                status=400, message=("User does not exist or has not signed "
                                     "up to use Notify.UW"))
        except InvalidAdminException as ex:
            return self.error_response(status=403, message="%s" % ex)

        return self.json_response(response_json)
