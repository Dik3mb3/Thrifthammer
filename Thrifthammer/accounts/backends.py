"""
Custom authentication backend for ThriftHammer.

Allows users to log in with either their username OR their email address,
in addition to the standard Django username-based login.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate against username or email address.

    Usage: add 'accounts.backends.EmailOrUsernameBackend' to
    AUTHENTICATION_BACKENDS in settings.py.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Try to find a user by username or email, then check the password.

        Returns the user on success, None on failure.
        """
        if username is None or password is None:
            return None

        try:
            # Case-insensitive match on username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.MultipleObjectsReturned:
            # If two accounts share an email, fall back to username-only match
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None
        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
