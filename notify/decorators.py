# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from uw_saml.decorators import group_required
from time import time


def restrict_session_to_weblogin_timeout(func):
    def wrapped(request, *args, **kwargs):
        if "session_start_time" not in request.session:
            request.session["session_start_time"] = time()

        now = time()
        session_start = request.session["session_start_time"]
        session_max = getattr(settings, 'MAX_SESSION_SPAN', 60 * 60 * 8)

        if (now - session_start) > session_max:
            # Make the user anonymous to force a login
            request.user = AnonymousUser()
            del request.session["session_start_time"]

        return func(request, *args, **kwargs)

    return wrapped
