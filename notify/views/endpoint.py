from uw_pws import PWS
from uw_nws import NWS
from uw_nws.exceptions import InvalidUUID
from uw_nws.models import Endpoint, Person
from userservice.user import UserService
from restclients_core.exceptions import DataFailureException
from notify.utilities import netid_from_eppn, get_person
from notify.views.rest_dispatch import RESTDispatch
import json
import logging


logger = logging.getLogger(__name__)


class EndpointView(RESTDispatch):
    def valid_user(self, user):
        return UserService().get_user() == user

    def GET(self, request, user):
        if not self.valid_user(user):
            return self.error_response(
                status=401, message="User not authenticated")

        try:
            person = get_person(user)
        except DataFailureException es ex:
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        endpoints_json = {}
        for endpoint in person.endpoints:
            is_valid = (endpoint.status.lower() != 'invalid')
            is_confirmed = (endpoint.status.lower() == 'verified')
            is_blacklisted = (endpoint.status.lower() == 'blacklisted' and
                              not endpoint.active)
            if endpoint.protocol.lower() == 'sms':
                sms = endpoint.endpoint_address
                sms = sms.replace("+1", "")
                sms = '-'.join((sms[:3], sms[3:6], sms[6:]))
                endpoint.endpoint_address = sms

            endpoints_json[endpoint.protocol.lower()] = {
                'EndpointID': endpoint.endpoint_id,
                'EndpointAddress': endpoint.endpoint_address,
                'Protocol': endpoint.protocol,
                'isBlacklisted': is_blacklisted,
                'isValid': is_valid,
                'isConfirmed': is_confirmed
            }

        if not endpoints_json:
            # Format emails at @uw.edu per CAN-930
            eppn = UserService().get_user()
            eppn = eppn.replace('@washington.edu', '@uw.edu')
            endpoints_json['DefaultEndpoint'] = {'EndpointAddress': eppn}

        return self.json_response(endpoints_json)

    def POST(self, request, user):
        if not self.valid_user(user):
            return self.error_response(
                status=401, message="User not authenticated")

        try:
            person = get_person(user)
        except DataFailureException es ex:
            msg = "Endpoint addition attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        request_json = request.raw_post_data
        request_obj = json.loads(request_json)
        protocol = request_obj['Protocol']

        nws = NWS(UserService().get_acting_user())
        try:
            endpoint = Endpoint()
            endpoint.owner = person.surrogate_id
            endpoint.user = person.surrogate_id
            endpoint.endpoint_address = request_obj['EndpointAddress']
            endpoint.protocol = protocol
            nws.create_endpoint(endpoint)

        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(
                    status=403, message="Unauthorized")

            return self.error_response(
                status=500, message="Error creating endpoint")

        for ep in person.endpoints:
            if ep.protocol.lower() == protocol.lower():
                endpoint = ep

        return self.json_response(endpoint.json_data())

    def PUT(self, request, user):
        if not self.valid_user(user):
            return self.error_response(
                status=401, message="User not authenticated")

        try:
            person = get_person(user)
        except DataFailureException es ex:
            msg = "Endpoint update attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        request_json = request.raw_post_data
        request_obj = simplejson.loads(request_json)
        endpoint_id = request_obj['EndpointID']
        endpoint = None
        for ep in person.endpoints.view_models:
            if ep.endpoint_id == endpoint_id:
                endpoint = ep

        if endpoint is None:
            return self.error_response(
                status=404, message="Endpoint '%s' not found" % endpoint_id)

        nws = NWS(user_service.get_acting_user())
        try:
            endpoint.endpoint_address = request_obj['EndpointAddress']
            response = nws.update_endpoint(endpoint)
        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(status=403, message="%s" % ex.msg)

            return self.error_response(
                status=500, message="Error creating endpoint")

        return self.json_response(endpoint.json_data())

    def DELETE(self, request, user):
        if not self.valid_user(user):
            return self.error_response(
                status=401, message="User not authenticated")

        try:
            person = get_person(user)
        except DataFailureException es ex:
            msg = "Endpoint deletion attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        nws = NWS(user_service.get_acting_user())
        try:
            request_json = request.raw_post_data
            request_obj = simplejson.loads(request_json)

            nws.delete_endpoint(request_obj['EndpointID'])

        except InvalidUUID as ex:
            return self.error_response(status=400, message="Invalid endpoint")

        except DataFailureException as ex:
            if ex.status != 410:
                return self.error_response(
                    status=500, message="Delete endpoint failed: %s" % ex.msg)

        return self.json_response({"message": "success"})


class ResendSMSConfirmationView(RESTDispatch):
    def POST(self, request):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException es ex:
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        endpoint = None
        for ep in person.endpoints:
            if ep.protocol.lower() == 'sms':
                endpoint = ep

        if endpoint is None:
            msg = ("Resend SMS verification requested for '{0}', "
                   "but no endpoint found").format(user)
            logger.warning(msg)
            return self.error_response(status=409, message=msg)

        if endpoint.active and endpoint.status.lower() == 'verified':
            msg = "Endpoint is already active and verified"
            status_code = 200
        else:
            try:
                status_code = NWS().resend_sms_endpoint_verification(
                    endpoint.endpoint_id)
                msg = "OK" if (status_code == 202) else "unknown condition"
            except DataFailureException as ex:
                msg = "Failed to request verification resend: %s" % ex.msg
                status_code = 500

        return self.json_response({"status": status_code, "message": msg})


class ToSConfirmation(RESTDispatch):
    def POST(self, request, user):
        user_service = UserService()
        if UserService().get_user() != user:
            return self.error_response(
                status=401, message="User not authenticated")

        try:
            person = get_person(user)
            person.attributes["AcceptedTermsOfUse"] = True

            try:
                NWS().update_person(person)
            except DataFailureException as ex:
                return self.error_response(
                    status=500, message="Update person failed: %s" % ex.msg)

        except DataFailureException es ex:
            if ex.status != 404:
                return self.error_response(
                    status=ex.status, message="Error: %s" % ex.msg)

            pws_person = PWS().get_person_by_netid(netid_from_eppn(user))

            person = Person()
            person.person_id = pws_person.uwregid
            person.surrogate_id = user
            person.default_endpoint_id = None
            person.attributes["AcceptedTermsOfUse"] = True

            try:
                nws.create_person(person)
            except DataFailureException as ex:
                return self.error_response(
                    status=500, message="Create person failed: %s" % ex.msg)

        return self.json_response({"status": 200, "message": "OK"})
