"""
Custom exceptions used by Notify.UW
"""


class InvalidUser(Exception):
    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return _("Invalid identifier %s" % self.identifier)