from django.contrib import auth
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import User, Permission
from django.contrib.auth.backends import RemoteUserBackend


class RemoteUserOverrideBackend(RemoteUserBackend):
    """
    This backend replaces the default RemoteUserBackend and allows an override
    user to be specified in the project settings for devlopment tasks.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, remote_user):

        if hasattr(settings, 'OVERRIDE_USER'):
            remote_user = settings.OVERRIDE_USER
        if not remote_user:
            return
        user = None
        username = self.clean_username(remote_user)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user = self.configure_user(user)
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        return user
