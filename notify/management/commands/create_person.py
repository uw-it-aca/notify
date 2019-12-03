from django.core.management.base import BaseCommand, CommandError
from notify.utilities import create_person


class Command(BaseCommand):
    help = "Creates a person"
    args = "<uwnetid>"

    def add_arguments(self, parser):
        parser.add_argument('uwnetid')

    def handle(self, *args, **options):
        uwnetid = options['uwnetid']
        person = create_person("@".join([uwnetid, "washington.edu"]))
