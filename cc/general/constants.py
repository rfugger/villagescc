"Generally useful constants."

from django.contrib.auth.models import User

MAX_USERNAME_LENGTH = User._meta.get_field_by_name('username')[0].max_length

