"Custom auth backend."

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class CaseInsensitiveModelBackend(ModelBackend):
    "Treats usernames as case-insensitive for logging in."
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
