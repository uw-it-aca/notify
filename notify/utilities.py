from restclients.nws import NWS
from restclients.sws import SWS
from restclients.pws import PWS
from restclients.exceptions import DataFailureException
from django.core.exceptions import PermissionDenied
from datetime import datetime
import json
import logging
import re


logger = logging.getLogger(__name__)


def get_channel_details_by_channel_id(channel_id):
    nws = NWS()
    try:
        channel = nws.get_channel_by_channel_id(channel_id)
    except Exception:
        raise

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

    sws = SWS()
    section = None
    try:
        section = sws.get_section_by_label(section_label)
        section_status = sws.get_section_status_by_label(section_label)
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
        for endpoint in person.endpoints.view_models:
            endpoints[endpoint.protocol] = True
    return json.dumps(endpoints)


def get_verified_endpoints_by_protocol(user_id):
    nws = NWS()
    verified_endpoints = {}
    try:
        endpoints = nws.get_endpoints_by_subscriber_id(user_id)
        for endpoint in endpoints:
            if (endpoint.status == 'verified'):
                verified_endpoints[endpoint.protocol.lower()] = endpoint
    except DataFailureException as ex:
        pass
    except Exception as ex:
        logger.exception(ex)
    return verified_endpoints


def netid_from_eppn(eppn):
    match = re.split("@", eppn)
    return match[0]


def getOpenRegistrationPeriods():
        channel_type = 'uw_student_courseavailable'
        try:
            nws = NWS()
            terms = nws.get_terms_with_active_channels(channel_type)
            terms_json = []
            for term in terms:
                term_json = term.json_data()
                terms_json.append(term_json)
            return json.dumps(terms_json)
        except DataFailureException as ex:
            pass


# get person, trying the following:
#   NWS by surrogate_id/netid
#   PWS by netid to get uwregid
#   NWS by uwregid
def get_person(user_id):
    person = None
    pws_person = None
    nws = NWS()
    try:
        pws = PWS()
        pws_person = pws.get_person_by_netid(netidFromEPPN(user_id))
    except:
        raise PermissionDenied
    try:
        person = nws.get_person_by_uwregid(pws_person.uwregid)
        # Update surrogate ID when user changes NETID
        if person.surrogate_id != user_id:
            person.surrogate_id = user_id
            nws = NWS()
            nws.update_person(person)
    except:
        pass
    return person


def user_accepted_tos(person):
    attr_list = person.get_attributes()
    if attr_list is None:
        return False
    for attribute in person.get_attributes():
        if "AcceptedTermsOfUse" == attribute.name:
            return attribute.value
    return False


def get_quarter_index(quarter):
    quarters = ['winter', 'spring', 'summer', 'autumn']
    return quarters.index(quarter.lower())
