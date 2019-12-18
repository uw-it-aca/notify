from django.conf import settings
from uw_sws import QUARTER_SEQ
from uw_sws.term import get_current_term, get_term_after


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
