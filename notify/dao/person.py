# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from uw_pws import PWS
from uw_nws import NWS
from uw_nws.models import Person
from restclients_core.exceptions import InvalidNetID, DataFailureException
from notify.exceptions import InvalidUser


def netid_from_eppn(eppn):
    return eppn.split("@")[0]


def get_person_by_netid(uwnetid):
    return PWS().get_person_by_netid(uwnetid)


def get_person_by_eppn(eppn):
    return get_person_by_netid(netid_from_eppn(eppn))


def get_person_by_regid(regid):
    return NWS().get_person_by_uwregid(regid)


def get_person(user_id):
    try:
        uwregid = get_person_by_eppn(user_id).uwregid
    except DataFailureException as ex:
        if ex.status == 400 or ex.status == 404:
            raise InvalidUser(user_id)
        else:
            raise

    person = None
    nws = NWS()
    try:
        person = nws.get_person_by_uwregid(uwregid)
        # Update surrogate ID when user changes NETID
        if person.surrogate_id != user_id:
            person.surrogate_id = user_id
            nws.update_person(person)
    except DataFailureException as err:
        pass
    return person


def create_person(user_id, attributes={}, act_as=None):
    person = Person()
    person.person_id = get_person_by_eppn(user_id).uwregid
    person.surrogate_id = user_id
    person.default_endpoint_id = None
    person.attributes = attributes
    return NWS(actas_user=act_as).create_person(person)


def update_person(person, act_as=None):
    NWS(actas_user=act_as).update_person(person)
