# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from uw_nws import NWS
from uw_nws.models import Subscription


def get_subscriptions_by_subscriber_id(subscriber_id):
    return NWS().get_subscriptions_by_subscriber_id(
        subscriber_id,
        max_results=getattr(settings, 'SUBSCRIPTION_SEARCH_MAX_RESULTS', 100))


def get_subscriptions_by_channel_id_and_subscriber_id(
        channel_id, subscriber_id):
    return NWS().get_subscriptions_by_channel_id_and_subscriber_id(
        channel_id, subscriber_id)


def get_subscription_by_channel_id_and_endpoint_id(channel_id, endpoint_id):
    return NWS().get_subscription_by_channel_id_and_endpoint_id(
        channel_id, endpoint_id)


def get_subscriptions_by_channel_id_and_person_id(channel_id, person_id):
    return NWS().get_subscriptions_by_channel_id_and_person_id(
        channel_id, person_id)


def create_subscription(subscription, act_as=None):
    return NWS(actas_user=act_as).create_subscription(subscription)


def delete_subscription(subscription_id, act_as=None):
    return NWS(actas_user=act_as).delete_subscription(subscription_id)
