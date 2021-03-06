# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

#
#  UW Course Availabilty Unsubscriber
#

from notify.events import NotifyEventProcessor
from notify.dao.channel import CHANNEL_TYPE
from notify.dao.subscription import (
    get_subscriptions_by_channel_id_and_person_id, delete_subscription)
from restclients_core.exceptions import DataFailureException


class EnrollmentProcessor(NotifyEventProcessor):
    """
    Collects enrollment event described by
    https://wiki.cac.washington.edu/display/StudentEvents/UW+Course+Enrollment+v2
    """
    # Enrollment Version 2 settings
    QUEUE_SETTINGS_NAME = 'ENROLLMENT_V2'

    # What we expect in a v2 enrollment message
    _eventMessageType = 'uw-student-registration-v2'
    _eventMessageVersion = '2'

    def process_message_body(self, json_data):
        for event in json_data.get('Events', []):
            action_code = event['Action']['Code'].upper()
            if action_code == 'A':
                reg_id = event['Person']['UWRegID']
                section_data = event['Section']
                course_data = section_data['Course']

                surrogate_id = ','.join([
                    course_data['Year'],
                    course_data['Quarter'].lower(),
                    course_data['CurriculumAbbreviation'].lower(),
                    course_data['CourseNumber'],
                    section_data['SectionID'].lower()])

                channel_id = '|'.join([CHANNEL_TYPE, surrogate_id])

                # Unsubscribe reg_id from channel_id
                try:
                    subs = get_subscriptions_by_channel_id_and_person_id(
                        channel_id, reg_id)
                    for sub in subs:
                        delete_subscription(sub.subscription_id)
                        self.logger.info('DELSUB to {} for {}'.format(
                            sub.subscription_id, reg_id))

                except DataFailureException as err:
                    if err.status == 400 or err.status == 404:
                        self.logger.info('NOSUB to {} for {}'.format(
                            channel_id, reg_id))
                    else:
                        self.logger.error(err)
                except Exception as err:
                    self.logger.error(err)
