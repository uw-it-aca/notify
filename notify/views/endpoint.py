# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from userservice.user import UserService
from restclients_core.exceptions import DataFailureException
from notify.dao.person import get_person, create_person, update_person
from notify.dao.endpoint import (
    Endpoint, create_endpoint, update_endpoint, delete_endpoint,
    resend_sms_endpoint_verification)
from notify.views.rest_dispatch import RESTDispatch
from notify.exceptions import InvalidUser, InvalidUUID
import json
import logging

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class EndpointView(RESTDispatch):
    def get(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)

            # Catch AttributeError below if person is None
            endpoints = person.endpoints
        except DataFailureException as ex:
            return self.error_response(
                status=500, message="Service unavailable")
        except (AttributeError, InvalidUser):
            return self.error_response(
                status=404, message="Person '{}' not found".format(user))

        sender_address = getattr(settings, 'SENDER_ADDRESS', '')
        endpoints_json = {}
        for endpoint in endpoints:
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
            email = user.replace('@washington.edu', '@uw.edu')
            endpoints_json['DefaultEndpoint'] = {'EndpointAddress': email}

        return self.json_response(endpoints_json)

    def post(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
            msg = "Endpoint addition failed for non-existent user '{}'".failed(
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '{}' not found".format(user))

        request_obj = json.loads(request.body)
        protocol = request_obj['Protocol']

        orig_user = UserService().get_original_user()
        try:
            endpoint = Endpoint()
            endpoint.owner = person.surrogate_id
            endpoint.subscriber_id = person.surrogate_id
            endpoint.endpoint_address = request_obj['EndpointAddress']
            endpoint.protocol = protocol
            create_endpoint(endpoint, act_as=orig_user)
            logger.info("CREATE endpoint {}".format(endpoint.endpoint_address))

        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(
                    status=403, message="Unauthorized")
            elif ex.status == 400:
                return self.error_response(
                    status=400, message="Invalid endpoint")

            logger.warning(ex)
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
            msg = "Endpoint update failed for non-existent user '{}'".format(
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '{}' not found".format(user))

        request_obj = json.loads(request.body)
        endpoint_id = request_obj['EndpointID']
        endpoint = None
        for ep in person.endpoints:
            if ep.endpoint_id == endpoint_id:
                endpoint = ep

        if endpoint is None:
            return self.error_response(
                status=404, message="Endpoint '{}' not found".format(
                    endpoint_id))

        orig_user = UserService().get_original_user()
        try:
            endpoint.endpoint_address = request_obj['EndpointAddress']
            update_endpoint(endpoint, act_as=orig_user)
            logger.info("UPDATE endpoint {}".format(endpoint.endpoint_address))
        except DataFailureException as ex:
            if ex.status == 403:
                return self.error_response(status=403, message=ex.msg)

            logger.warning(ex)
            return self.error_response(
                status=500, message="Error creating endpoint")

        return self.json_response(endpoint.json_data())

    def delete(self, request, *args, **kwargs):
        user = UserService().get_user()
        try:
            person = get_person(user)
        except DataFailureException as ex:
            msg = "Endpoint deletion failed for non-existent user '{}'".format(
                user)
            logger.warning(msg)
            return self.error_response(
                status=404, message="Person '{}' not found".format(user))

        orig_user = UserService().get_original_user()
        try:
            request_obj = json.loads(request.body)
            endpoint_id = request_obj['EndpointID']
            delete_endpoint(endpoint_id, act_as=orig_user)
            logger.info("DELETE endpoint {}".format(endpoint_id))

        except InvalidUUID as ex:
            return self.error_response(status=400, message="Invalid endpoint")

        except DataFailureException as ex:
            if ex.status != 410:
                logger.warning(ex)
                return self.error_response(
                    status=500, message="Delete endpoint failed: {}".format(
                        ex.msg))

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
                status=404, message="Person '{}' not found".format(user))

        endpoint = None
        for ep in person.endpoints:
            if ep.protocol.lower() == 'sms':
                endpoint = ep

        if endpoint is None:
            msg = ("Resend SMS verification requested for '{}', "
                   "but no endpoint found").format(user)
            logger.warning(msg)
            return self.error_response(status=409, message=msg)

        if endpoint.active and endpoint.status.lower() == 'verified':
            msg = "Endpoint is already active and verified"
            status_code = 200
        else:
            try:
                status_code = resend_sms_endpoint_verification(
                    endpoint.endpoint_id)
                if status_code == 202:
                    logger.info("RESEND endpoint verification {}".format(
                        endpoint.endpoint_id))
                    msg = "OK"
                else:
                    msg = "unknown condition"
            except DataFailureException as ex:
                logger.warning(ex)
                msg = "Failed to request verification resend: {}".format(
                    ex.msg)
                status_code = 500

        return self.json_response({"status": status_code, "message": msg})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ToSConfirmation(RESTDispatch):
    def post(self, request, *args, **kwargs):
        user = UserService().get_user()
        original_user = UserService().get_original_user()
        try:
            person = get_person(user)

            # Catch AttributeError below if person is None
            person.attributes["AcceptedTermsOfUse"] = True

            try:
                update_person(person, act_as=original_user)
                logger.info("UPDATE person '{}', accepted ToS".format(user))
            except DataFailureException as ex:
                logger.warning("UPDATE person '{}' failed: {}".format(
                    user, ex))
                return self.error_response(
                    status=500, message="Update person failed: {}".format(
                        ex.msg))

        except InvalidUser:
            return self.error_response(
                status=404, message="Person '{}' not found".format(user))

        except (AttributeError, DataFailureException) as ex:
            try:
                create_person(
                    user, attributes={"AcceptedTermsOfUse": True},
                    act_as=original_user)
                logger.info("CREATE person '{}', accepted ToS".format(user))
            except DataFailureException as ex:
                logger.warning("CREATE person '{}' failed: {}".format(
                    user, ex))
                return self.error_response(
                    status=500, message="Create person failed: {}".format(
                        ex.msg))

        return self.json_response({"status": 200, "message": "OK"})
