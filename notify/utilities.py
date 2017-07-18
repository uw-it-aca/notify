from uw_nws import NWS
from uw_nws.models import Person
from uw_pws import PWS
from uw_sws.section import get_section_by_label
from uw_sws.section_status import get_section_status_by_label
from uw_sws.term import get_current_term, get_term_after
from restclients_core.exceptions import DataFailureException
from datetime import datetime
import json
import logging
import re


logger = logging.getLogger(__name__)


def get_channel_details_by_channel_id(channel_id):
    channel = NWS().get_channel_by_channel_id(channel_id)
    return get_course_details_by_channel(channel)


def get_course_details_by_channel(channel):
    section_label = ""
    try:
        parts = channel.surrogate_id.split(",")
        if (len(parts) == 5):
            parts[2] = parts[2].upper()
            section_id = parts.pop().upper()
            section_label = ",".join(parts) + "/" + section_id
        else:
            raise Exception('Invalid surrogate id')
    except Exception as ex:
        logger.exception(ex)
        return {'course_title': 'No Course Found'}

    section = None
    try:
        section = get_section_by_label(section_label)
        section_status = get_section_status_by_label(section_label)
    except DataFailureException as ex:
        return {'course_title': 'No section info found'}
    except Exception as ex:
        logger.exception(ex)
        return {'course_title': 'No section info found'}

    course_abbr = "%s %s %s" % (section.curriculum_abbr, section.course_number,
                                section.section_id)

    # build meetings object
    meetings = []
    for meeting in section.meetings:
        meeting_json = meeting.json_data()
        cleaned_instructors = []
        for inst in meeting.instructors:
            if inst.TSPrint:
                cleaned_instructor = {'first_name': inst.first_name,
                                      'surname': inst.surname}
                cleaned_instructors.append(cleaned_instructor)
        meeting_json['instructors'] = cleaned_instructors
        if len(cleaned_instructors) > 0:
            meeting_json['has_instructors'] = True
        else:
            meeting_json['has_instructors'] = False
        if meeting.building_to_be_arranged and meeting.room_to_be_arranged:
            meeting_json['location_tbd'] = True
        # format meeting times
        try:
            start_time = datetime.strptime(meeting_json['start_time'], "%H:%M")
            meeting_json['start_time'] = start_time.strftime("%-I:%M%p")
            end_time = datetime.strptime(meeting_json['end_time'], "%H:%M")
            meeting_json['end_time'] = end_time.strftime("%-I:%M%p")
        except:
            pass
        meetings.append(meeting_json)

    response = {'course_title': section.course_title_long,
                'course_abbr': course_abbr, 'section_sln': section.sln,
                'meetings': meetings,
                'current_enrollment': section_status.current_enrollment,
                'total_seats': section_status.limit_estimated_enrollment,
                'add_code_required': section_status.add_code_required,
                'faculty_code_required': section_status.faculty_code_required}
    return response


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


def netid_from_eppn(eppn):
    match = re.split("@", eppn)
    return match[0]


def get_open_registration_periods(term=None):
    # Check the passed term, and the next 3, to see if they have
    # a channel for any course in that term.
    # when the sws term resource provides us with a timeschedule publish
    # date, use that instead of this.
    channel_type = 'uw_student_courseavailable'
    if term is None:
        term = get_current_term()

    terms = [term]
    for i in range(3):
        term = get_term_after(term)
        terms.append(term)

    active_terms = []
    nws = NWS()
    for term in terms:
        channels = nws.get_active_channels_by_year_quarter(
            channel_type, term.year, term.quarter)
        if len(channels):
            active_terms.append(term)

    return active_terms


# get person, trying the following:
#   PWS by netid to get uwregid
#   NWS by uwregid
def get_person(user_id):
    person = None

    try:
        pws_person = PWS().get_person_by_netid(netid_from_eppn(user_id))
    except DataFailureException as err:
        raise

    nws = NWS()
    try:
        person = nws.get_person_by_uwregid(pws_person.uwregid)
        # Update surrogate ID when user changes NETID
        if person.surrogate_id != user_id:
            person.surrogate_id = user_id
            nws.update_person(person)
    except DataFailureException as err:
        pass
    return person


def create_person(user_id, attributes={}):
    pws_person = PWS().get_person_by_netid(netid_from_eppn(user_id))

    person = Person()
    person.person_id = pws_person.uwregid
    person.surrogate_id = user_id
    person.default_endpoint_id = None
    person.attributes = attributes

    return NWS().create_person(person)


def user_accepted_tos(person):
    return person.attributes.get("AcceptedTermsOfUse", False)


def get_quarter_index(quarter):
    quarters = ['winter', 'spring', 'summer', 'autumn']
    return quarters.index(quarter.lower())
