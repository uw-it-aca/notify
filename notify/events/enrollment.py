#
#  UW Course Availabilty Unsubscriber
#

from notify.events import EventBase
from restclients_core.exceptions import DataFailureException
from uw_nws import NWS


class Enrollment(EventBase):
    """
    Collects enrollment event described by
    https://wiki.cac.washington.edu/display/StudentEvents/UW+Course+Enrollment+v2
    """
    # Enrollment Version 2 settings
    SETTINGS_NAME = 'ENROLLMENT_V2'
    EXCEPTION_CLASS = EventException

    # What we expect in a v2 enrollment message
    _eventMessageType = 'uw-student-registration-v2'
    _eventMessageVersion = '2'

    def process_events(self, events):
        for event in events['Events']:
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

                channel_id = '|'.join([
                    'uw_student_courseavailable',
                    surrogate_id]);

                # Unsubscribe reg_id from channel_id
                nws = NWS()
                try:
                    subs = nws.get_subscriptions_by_channel_id_and_person_id(
                        channel_id, reg_id)
                    for sub in subs:
                        nws.delete_subscription(sub.subscription_id)
                        self._log.info('DELSUB to %s for %s', % (
                            sub.subscription_id, reg_id))

                except DataFailureException as err:
                    if err.status == 400 or err.status == 404:
                        self._log.info('NOSUB to %s for %s', % (
                            channel_id, reg_id))
                    else:
                        self._log.error('%s' % err)
                except Exception as err:
                    self._log.error('%s' % err)
