# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from uw_sws.section import get_section_by_label
from uw_sws.section_status import get_section_status_by_label
from uw_sws.exceptions import InvalidSectionID
from restclients_core.exceptions import DataFailureException
from notify.dao.channel import get_channel_by_id
from datetime import datetime


def get_section_details_by_channel(channel):
    section_label = ''
    try:
        parts = channel.surrogate_id.split(',')
        if (len(parts) == 5):
            parts[2] = parts[2].upper()
            section_id = parts.pop().upper()
            section_label = ','.join(parts) + '/' + section_id
        else:
            raise Exception('Invalid surrogate id')
    except Exception as ex:
        return {'course_title': 'No Course Found'}

    section = None
    try:
        section = get_section_by_label(section_label)
        section_status = get_section_status_by_label(section_label)
    except DataFailureException as ex:
        return {'course_title': 'No section info found'}
    except InvalidSectionID as ex:
        return {'course_title': 'Invalid section'}
    except Exception as ex:
        return {'course_title': 'No section info found'}

    course_abbr = ' '.join([
        section.curriculum_abbr, section.course_number, section.section_id])

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
        except Exception:
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


def get_section_details_by_channel_id(channel_id):
    return get_section_details_by_channel(get_channel_by_id(channel_id))
