from notify.utilities import get_person, user_accepted_tos, user_has_valid_endpoints
from userservice.user import UserService
from django.conf import settings


def notify_context(request):
    user_service = UserService()
    context = {'is_mobile': request.MOBILE,
               'override_user': user_service.get_override_user(),
               'netid': None,
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
