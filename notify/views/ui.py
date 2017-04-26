from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.conf import settings
from restclients_core.exceptions import DataFailureException
from notify.utilities import (
    get_open_registration_periods, get_person, user_accepted_tos,
    user_has_valid_endpoints)
from notify.decorators import restrict_session_to_weblogin_timeout
from userservice.user import UserService
from authz_group import Group
from uw_nws import NWS
import logging
import urlparse


# Get an instance of a logger
logger = logging.getLogger(__name__)


def build_view_context(request):
    user_service = UserService()
    context = {'is_mobile': request.is_mobile,
               'override_user': user_service.get_override_user(),
               'netid': None,
               'support_email': getattr(settings, 'SUPPORT_EMAIL', ''),
               'ANALYTICS_KEY': getattr(settings, 'GOOGLE_ANALYTICS_KEY')}

    if hasattr(settings, 'UI_SYSTEM_MESSAGE'):
        context['system_message'] = getattr(settings, 'UI_SYSTEM_MESSAGE')

    netid = user_service.get_user()
    if netid:
        person = get_person(netid)
        context['user_accepted_tos'] = True
        if person is None or user_accepted_tos(person) is False:
            context['user_accepted_tos'] = False
            # grab path requested for later redirection
            full_path = request.get_full_path()
            if full_path and full_path != '/':
                context['full_path'] = full_path
        context['netid'] = netid
        context['valid_endpoints'] = user_has_valid_endpoints(person)

    return context


@restrict_session_to_weblogin_timeout
@login_required
def home_view(request):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    context['reg_periods'] = get_open_registration_periods()
    return render(request, 'app.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def profile_view(request):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    return render(request, 'profile.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def find_view(request):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    context['reg_periods'] = getOpenRegistrationPeriods()
    return render(request, 'find.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def course_view(request, year, quarter, sln):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    context['reg_periods'] = get_open_registration_periods()
    context['year'] = year
    context['quarter'] = quarter
    context['sln'] = sln
    return render(request, 'course.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def detail_view(request, channel_id):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)

    try:
        channel = NWS().get_channel_by_channel_id(channel_id)
        context['class_name'] = channel.name
        context['description'] = channel.description
    except DataFailureException as ex:
        context['class_name'] = 'No class found'
        context['description'] = 'Invalid channel id {0}'.format(channel_id)

    return render(request, 'class_details.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def confirm_view(request):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    return render(request, 'confirm_subscription.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def unsubscribe_view(request, channel_id):
    context = build_view_context(request)
    if context.get('user_accepted_tos', False) is False:
        return redirect_to_terms_of_service(context)
    return render(request, 'confirm_unsubscribe.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def tos_view(request):
    context = build_view_context(request)
    redirect_path = request.GET.get('next', None)
    if redirect_path is not None:
        context['redirect_path'] = redirect_path
    return render(request, 'terms_of_service.html', context)


@restrict_session_to_weblogin_timeout
@login_required
def admin(request):
    actual_user = UserService().get_original_user()
    g = Group()
    is_admin = g.is_member_of_group(
        actual_user, getattr(settings, 'USERSERVICE_ADMIN_GROUP'))

    if is_admin is False:
        return HttpResponseRedirect("/")

    return render(request, 'admin/menu.html', {})


# Based on django.contrib.auth.views.login
def shib_redirect(request):
    if not request.user or not request.user.is_authenticated():
        if settings.DEBUG:
            user = auth.authenticate(remote_user="javerage@washington.edu")
            if user:
                # User is valid.  Set request.user and persist user in the
                # session by logging the user in.
                request.user = user
                auth.login(request, user)

    if not request.user:
        raise Exception("Error: no user in request")

    redirect_to = request.GET.get("next", '')

    netloc = urlparse.urlparse(redirect_to)[1]

    # Use default setting if redirect_to is empty
    if not redirect_to:
        redirect_to = "/"

    # Heavier security check -- don't allow redirection to a different
    # host.
    elif netloc and netloc != request.get_host():
        redirect_to = "/"

    return HttpResponseRedirect(redirect_to)


def redirect_to_terms_of_service(context):
    tos_path = '/tos/'
    full_path = context.get('full_path', None)
    if full_path:
        tos_path += '?next=' + full_path
    return HttpResponseRedirect(tos_path)
