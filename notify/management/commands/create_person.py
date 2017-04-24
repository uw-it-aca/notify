from django.core.management.base import BaseCommand, CommandError
from notify.utilities import create_person


class Command(BaseCommand):
    help = "Creates a person"
    args = "<uwnetid>"

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError("Usage: create_person <uwnetid>")

        uwnetid = args[0]

        person = create_person("%s@%s" % (uwnetid, "washington.edu"))
