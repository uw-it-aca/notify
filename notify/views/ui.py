# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.views.generic.base import TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from restclients_core.exceptions import DataFailureException
from notify.dao.term import get_open_registration_periods
from notify.dao.person import get_person
from notify.dao.channel import get_channel_by_id
from notify.exceptions import InvalidUser, InvalidUUID
from userservice.user import UserService
from persistent_message.models import Message
import json


class AdminView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect('/support')


@method_decorator(login_required, name='dispatch')
class NotifyView(TemplateView):
    def get_context_data(self, **kwargs):
        user_service = UserService()
        context = {
            'is_mobile': self.request.user_agent.is_mobile,
            'override_user': user_service.get_override_user(),
            'valid_login': False,
            'netid': None,
            'user_accepted_tos': False,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', ''),
            'ANALYTICS_KEY': getattr(settings, 'GOOGLE_ANALYTICS_KEY', ''),
            'messages': [],
            'year': kwargs.get('year'),
            'quarter': kwargs.get('quarter'),
            'sln': kwargs.get('sln'),
        }

        for message in Message.objects.active_messages():
            if 'message_level' not in context:
                context['message_level'] = message.get_level_display().lower()
            context['messages'].append(message.render())

        netid = user_service.get_user()
        if netid:
            person = None
            try:
                person = get_person(netid)
                context['valid_login'] = True
                context['netid'] = netid

                if person is not None and person.accepted_tos():
                    context['user_accepted_tos'] = True
                    context['valid_endpoints'] = json.dumps(
                        person.has_valid_endpoints())

                    reg_periods = get_open_registration_periods()
                    context['has_reg_periods'] = len(reg_periods)
                    context['reg_periods'] = json.dumps(reg_periods)

            except InvalidUser:
                pass

        return context

    def render_to_response(self, context, **response_kwargs):
        if not context.get('user_accepted_tos'):
            return HttpResponseRedirect('{}?next={}'.format(
                reverse('tos'), self.request.get_full_path()))

        return super(NotifyView, self).render_to_response(
            context, **response_kwargs)


class HomeView(NotifyView):
    template_name = 'app.html'


class ProfileView(NotifyView):
    template_name = 'profile.html'


class FindView(NotifyView):
    template_name = 'find.html'


class CourseView(NotifyView):
    template_name = 'course.html'


class DetailView(NotifyView):
    template_name = 'class_details.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        channel_id = kwargs.get('channel_id')
        try:
            channel = get_channel_by_id(channel_id)
            context['class_name'] = channel.name
            context['description'] = channel.description
        except (InvalidUUID, DataFailureException) as ex:
            context['class_name'] = 'No class found'
            context['description'] = 'Invalid channel ID {}'.format(channel_id)
        return self.render_to_response(context)


class ConfirmView(NotifyView):
    template_name = 'confirm_subscription.html'


class UnsubscribeView(NotifyView):
    template_name = 'confirm_unsubscribe.html'


class ToSView(NotifyView):
    template_name = 'terms_of_service.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['redirect_path'] = request.GET.get('next')
        return super(NotifyView, self).render_to_response(context)
