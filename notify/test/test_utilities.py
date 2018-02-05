from django.test import TestCase
from notify.utilities import (
    netid_from_eppn, user_accepted_tos, get_quarter_index,
    user_has_valid_endpoints)
from uw_sws.term import get_current_term, get_term_after
from uw_sws.util import fdao_sws_override
from uw_pws.models import Person
from uw_nws.models import Endpoint


class TestNetid(TestCase):
    def test_netid_from_eppn(self):
        self.assertEquals(netid_from_eppn('j@test.edu'), 'j')
        self.assertEquals(netid_from_eppn('j@test@edu'), 'j')
        self.assertEquals(netid_from_eppn('@test.edu'), '')
        self.assertEquals(netid_from_eppn('j'), 'j')
        self.assertEquals(netid_from_eppn('j:test.edu'), 'j:test.edu')


@fdao_sws_override
class TestQuarterIndex(TestCase):
    def test_get_quarter_index(self):
        self.assertEquals(get_quarter_index('summer'), 2)
        self.assertEquals(get_quarter_index('SPRING'), 1)
        self.assertRaises(ValueError, get_quarter_index, 'Fall')

        term = get_current_term()
        self.assertEquals(get_quarter_index(term.quarter), 1)

        term = get_term_after(term)
        self.assertEquals(get_quarter_index(term.quarter), 2)


class TestPersonAttributes(TestCase):
    def setUp(self):
        self.person = Person()
        self.person.attributes = {}
        self.person.endpoints = []

    def test_user_accepted_tos(self):
        self.assertEquals(user_accepted_tos(self.person), False)

        self.person.attributes['AcceptedTermsOfUse'] = True
        self.assertEquals(user_accepted_tos(self.person), True)

    def test_user_has_valid_endpoints(self):
        self.assertEquals(user_has_valid_endpoints(self.person),
                          '{"sms": false, "email": false}')

        self.person.endpoints.append(Endpoint(protocol='SMS'))
        self.assertEquals(user_has_valid_endpoints(self.person),
                          '{"sms": true, "email": false}')

        self.person.endpoints.append(Endpoint(protocol='Email'))
        self.assertEquals(user_has_valid_endpoints(self.person),
                          '{"sms": true, "email": true}')