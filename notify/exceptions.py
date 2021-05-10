# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from uw_nws.exceptions import InvalidUUID


class InvalidUser(Exception):
    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return "Invalid identifier {}".format(self.identifier)
