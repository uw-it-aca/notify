from django.test import TestCase
from notify.utilities import expires_datetime
from notify.dao.person import netid_from_eppn
from notify.dao.term import get_quarter_index
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


class TestExpiresDateTime(TestCase):
    def test_expires_datetime(self):
        with self.settings(
                CHANNEL_EXPIRES_AFTER=None):
            self.assertEquals(expires_datetime(), None)

        with self.settings(
                CHANNEL_EXPIRES_AFTER='2013-05-31T00:00:00'):
            self.assertEquals(expires_datetime().isoformat(),
                              '2013-05-31T00:00:00')

        with self.settings(
                CHANNEL_EXPIRES_AFTER='000000000'):
            self.assertRaises(ValueError, expires_datetime)
