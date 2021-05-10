# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from uw_nws import NWS
from uw_nws.models import Endpoint


def get_endpoints_by_subscriber_id(subscriber_id):
    return NWS().get_endpoints_by_subscriber_id(subscriber_id)


def get_endpoint_by_id(endpoint_id):
    return NWS().get_endpoint_by_endpoint_id(endpoint_id)


def get_endpoint_by_address(address):
    return NWS().get_endpoint_by_address(address)


def create_endpoint(endpoint, act_as=None):
    return NWS(actas_user=act_as).create_endpoint(endpoint)


def update_endpoint(endpoint, act_as=None):
    return NWS(actas_user=act_as).update_endpoint(endpoint)


def delete_endpoint(endpoint_id, act_as=None):
    return NWS(actas_user=act_as).delete_endpoint(endpoint_id)


def resend_sms_endpoint_verification(endpoint_id):
    return NWS().resend_sms_endpoint_verification(endpoint_id)
