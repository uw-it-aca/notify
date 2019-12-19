from django.conf import settings
from uw_nws import NWS
from uw_nws.models import Person
from restclients_core.exceptions import InvalidNetID, DataFailureException
from notify.dao.person import get_person_by_eppn
from notify.dao.section import get_section_details_by_channel
from notify.dao.term import get_open_terms
from notify.exceptions import InvalidUser
from datetime import datetime
import dateutil.parser
import json
import logging
import re


logger = logging.getLogger(__name__)


def get_channel_details_by_channel_id(channel_id):
    channel = NWS().get_channel_by_channel_id(channel_id)
    return get_section_details_by_channel(channel)


def user_has_valid_endpoints(person):
    endpoints = {'sms': False, 'email': False}
    if person is not None:
        for endpoint in person.endpoints:
            endpoints[endpoint.protocol.lower()] = True
    return json.dumps(endpoints)


def get_verified_endpoints_by_protocol(user_id):
    verified_endpoints = {}
    try:
        endpoints = NWS().get_endpoints_by_subscriber_id(user_id)
        for endpoint in endpoints:
            if (endpoint.status.lower() == 'verified'):
                verified_endpoints[endpoint.protocol.lower()] = endpoint
    except DataFailureException as ex:
        pass
    except Exception as ex:
        logger.exception(ex)
    return verified_endpoints


def expires_datetime():
    expires = getattr(settings, 'CHANNEL_EXPIRES_AFTER', None)
    if expires is not None:
        expires = dateutil.parser.parse(expires)
    return expires


def get_open_registration_periods(term=None):
    # Check the passed term, and the next 3, to see if they have
    # a channel for any course in that term.
    # when the sws term resource provides us with a timeschedule publish
    # date, use that instead of this.
    channel_type = 'uw_student_courseavailable'
    active_terms = []
    nws = NWS()
    for term in get_open_terms(term):
        channels = nws.get_active_channels_by_year_quarter(
            channel_type, term.year, term.quarter, expires=expires_datetime())
        if len(channels):
            term_json = term.json_data()
            active_terms.append({k: term_json[k] for k in ['year', 'quarter']})

    return json.dumps(active_terms)


# get person, trying the following:
#   PWS by netid to get uwregid
#   NWS by uwregid
def get_person(user_id):
    try:
        uwregid = get_person_by_eppn(user_id).uwregid
    except DataFailureException as ex:
        if ex.status == 400 or ex.status == 404:
            raise InvalidUser(user_id)
        else:
            raise

    person = None
    nws = NWS()
    try:
        person = nws.get_person_by_uwregid(uwregid)
        # Update surrogate ID when user changes NETID
        if person.surrogate_id != user_id:
            person.surrogate_id = user_id
            nws.update_person(person)
    except DataFailureException as err:
        pass
    return person


def create_person(user_id, attributes={}):
    person = Person()
    person.person_id = get_person_by_eppn(user_id).uwregid
    person.surrogate_id = user_id
    person.default_endpoint_id = None
    person.attributes = attributes
    return NWS().create_person(person)


def validate_override_user(username):
    if not len(username):
        return ("No override user supplied, please enter a user to override"
                "as in the format of [netid]@washington.edu")

    match = re.search('@washington.edu', username)
    if match:
        try:
            person = get_person_by_eppn(username)
        except (InvalidNetID, DataFailureException) as ex:
            return ("Override user could not be found in the PWS. "
                    "Please enter a valid user to override as in the "
                    "format of [netid]@washington.edu You entered: ")
    else:
        return ("Override user must be formatted as [netid]@washington.edu. "
                "You entered: ")
