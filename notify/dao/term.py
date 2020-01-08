from django.conf import settings
from uw_sws import QUARTER_SEQ
from uw_sws.term import get_current_term, get_term_after
from notify.dao.channel import get_active_channels_by_year_quarter


def get_quarter_index(quarter):
    return QUARTER_SEQ.index(quarter.lower())


def get_open_terms(term=None):
    if term is None:
        term = get_current_term()

    terms = [term]
    for i in range(getattr(settings, 'FUTURE_TERMS_TO_SEARCH', 3)):
        term = get_term_after(term)
        terms.append(term)

    return terms


def get_open_registration_periods(term=None):
    # Check the passed term, and the next 3, to see if they have
    # a channel for any course in that term.
    # when the sws term resource provides us with a timeschedule publish
    # date, use that instead of this.
    active_terms = []
    for term in get_open_terms(term):
        channels = get_active_channels_by_year_quarter(term.year, term.quarter)
        if len(channels):
            term_json = term.json_data()
            active_terms.append({k: term_json[k] for k in ['year', 'quarter']})
    return active_terms
