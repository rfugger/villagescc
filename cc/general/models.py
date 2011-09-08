from django.db import models

from south.modelsinspector import add_introspection_rules

class VarCharField(models.CharField):
    """
    A CharField where max length isn't enforced at the db level, so it can
    be modified without modifying the db.
    If max_length isn't passed to constructor, a huge default will be used.
    """
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            # Satisfy django management validation.
            kwargs['max_length'] = int(1e9)
        super(VarCharField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        # This has no function, since this value is used as a lookup in
        # db_type().  Put something that isn't known by django so it
        # raises an error if it is ever used.
        return 'CharField'

    def db_type(self, connection):
        # *** This is probably only compatible with Postgres.
        # 'varchar' with no max length is equivalent to 'text' in Postgres,
        # but put 'varchar' so we can tell VarCharFields from TextFields
        # when we're looking at the db.
        return 'varchar'    

class EmailField(models.EmailField):
    """
    An EmailField with the proper max_length.
    """
    # Maximum length of an email address string.
    # From http://www.dominicsayers.com/isemail/
    MAX_EMAIL_LENGTH = 254

    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = self.MAX_EMAIL_LENGTH
        super(EmailField, self).__init__(*args, **kwargs)
    
# Enable south migrations for custom fields.
add_introspection_rules([], ["^cc\.general"])

# *** HACK ALERT ***
# Load forms monkeypatch.
import cc.general.forms
