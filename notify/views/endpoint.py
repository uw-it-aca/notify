from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from uw_nws import NWS
from uw_nws.exceptions import InvalidUUID
from uw_nws.models import Endpoint
from userservice.user import UserService
from restclients_core.exceptions import DataFailureException
from notify.utilities import get_person, create_person
from notify.views.rest_dispatch import RESTDispatch
from notify.exceptions import InvalidUser
import json
import logging

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class EndpointView(RESTDispatch):
    def get(self, request, *args, **kwargs):
        user = kwargs.get('user')
        try:
            person = get_person(user)
        except DataFailureException as ex:
            return self.error_response(
                status=500, message="Service unavailable" % user)
        except InvalidUser:
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        sender_address = getattr(settings, 'SENDER_ADDRESS', '')
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
                'SenderAddress': sender_address,
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

    def post(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
            msg = "Endpoint addition attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        request_obj = json.loads(request.body)
        protocol = request_obj['Protocol']

        nws = NWS(UserService().get_acting_user())
        try:
            endpoint = Endpoint()
            endpoint.owner = person.surrogate_id
            endpoint.subscriber_id = person.surrogate_id
            endpoint.endpoint_address = request_obj['EndpointAddress']
            endpoint.protocol = protocol
            nws.create_endpoint(endpoint)

        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(
                    status=403, message="Unauthorized")
            elif ex.status == 400:
                return self.error_response(
                    status=400, message="Invalid endpoint")

            logger.warning(ex.msg)
            return self.error_response(
                status=500, message="Error creating endpoint")

        for ep in person.endpoints:
            if ep.protocol.lower() == protocol.lower():
                endpoint = ep

        return self.json_response(endpoint.json_data())

    def put(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
            msg = "Endpoint update attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        request_obj = json.loads(request.body)
        endpoint_id = request_obj['EndpointID']
        endpoint = None
        for ep in person.endpoints:
            if ep.endpoint_id == endpoint_id:
                endpoint = ep

        if endpoint is None:
            return self.error_response(
                status=404, message="Endpoint '%s' not found" % endpoint_id)

        nws = NWS(UserService().get_acting_user())
        try:
            endpoint.endpoint_address = request_obj['EndpointAddress']
            response = nws.update_endpoint(endpoint)
        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(status=403, message="%s" % ex.msg)

            logger.warning(ex.msg)
            return self.error_response(
                status=500, message="Error creating endpoint")

        return self.json_response(endpoint.json_data())

    def delete(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
            msg = "Endpoint deletion attempted for non-existent user '%s'" % (
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        nws = NWS(UserService().get_acting_user())
        try:
            request_obj = json.loads(request.body)

            nws.delete_endpoint(request_obj['EndpointID'])

        except InvalidUUID as ex:
            return self.error_response(status=400, message="Invalid endpoint")

        except DataFailureException as ex:
            if ex.status != 410:
                logger.warning(ex.msg)
                return self.error_response(
                    status=500, message="Delete endpoint failed: %s" % ex.msg)

        return self.json_response({"message": "success"})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ResendSMSConfirmationView(RESTDispatch):
    def post(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
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
                logger.warning(ex.msg)
                msg = "Failed to request verification resend: %s" % ex.msg
                status_code = 500

        return self.json_response({"status": status_code, "message": msg})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ToSConfirmation(RESTDispatch):
    def post(self, request, *args, **kwargs):
        user = kwargs.get('user')
        try:
            person = get_person(user)

            # Catch AttributeError below if person is None
            person.attributes["AcceptedTermsOfUse"] = True

            nws = NWS(UserService().get_acting_user())
            try:
                nws.update_person(person)
            except DataFailureException as ex:
                logger.warning(ex.msg)
                return self.error_response(
                    status=500, message="Update person failed: %s" % ex.msg)

        except InvalidUser:
            return self.error_response(
                status=404, message="Person '%s' not found" % user)

        except (AttributeError, DataFailureException) as ex:
            try:
                create_person(user, attributes={"AcceptedTermsOfUse": True})
            except DataFailureException as ex:
                logger.warning(ex.msg)
                return self.error_response(
                    status=500, message="Create person failed: %s" % ex.msg)

        return self.json_response({"status": 200, "message": "OK"})
