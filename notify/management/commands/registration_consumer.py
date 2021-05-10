# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

"""
This command reads UW registration events, and removes CAN subscriptions for
users who have signed up for a course.
"""

from django.core.management.base import BaseCommand, CommandError
from aws_message.gather import Gather, GatherException
from notify.events.enrollment import EnrollmentProcessor
from logging import getLogger

logger = getLogger(__name__)


class Command(BaseCommand):
    help = "Listens for registration events, and drops CAN subscriptions"

    def handle(self, *args, **options):
        try:
            Gather(processor=EnrollmentProcessor()).gather_events()
        except GatherException as err:
            logger.error("GATHER ERROR: {}".format(err))
