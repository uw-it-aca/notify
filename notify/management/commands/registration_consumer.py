"""
This command reads UW registration events, and removes CAN subscriptions for
users who have signed up for a course.
"""

from django.core.management.base import BaseCommand
from aws_message.gather import Gather, GatherException
from notify.events import Enrollment


class Command(BaseCommand):
    help = "Listens for registration events, and drops CAN subscriptions"

    def handle(self, *args, **options):
        try:
            Gather(processor=Enrollment).gather_events()
        except GatherException as err:
            raise CommandError(err)
        except Exception as err:
            raise CommandError('FAIL: %s' % err)
