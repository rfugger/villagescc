from django.contrib.gis.db import models
from django.core import serializers
from django.core.serializers.base import DeserializationError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# Import introspection rules to allow south to migrate geo fields.
from south.introspection_plugins import geodjango

from cc.general.models import VarCharField

class LocationDeserializationError(Exception):
    pass

class Location(models.Model):
    "A geographic location, named by neighborhood, city, state, country."

    # TODO: Possible optimizations for distance queries:
    # - use bounding box only (__bboverlaps or && operator)
    # - use planar projection rather than spherical coordinates
    # - use spheroid=False for geography queries (not needed on planar projection)
    
    point = models.PointField(geography=True)
    country = VarCharField(_("Country"))
    state = VarCharField(_("State/Province (Abbr.)"), blank=True)
    city = VarCharField(_("City"), blank=True)
    neighborhood = VarCharField(_("Neighbourhood"), blank=True)
    
    objects = models.GeoManager()

    def __unicode__(self):
        if self.city:
            name = self.city
            if self.neighborhood:
                name = "%s (%s)" % (name, self.neighborhood)
        else:
            name = self.country
            if self.state:
                name = "%s, %s" % (self.state, name)
        return name

    def full_name(self):
        names = []
        for field in ('neighborhood', 'city', 'state', 'country'):
            value = getattr(self, field)
            if value:
                names.append(value)
        return ', '.join(names)

    def to_session(self, request):
        "Makes this location the current location for this session."
        request.session[settings.LOCATION_SESSION_KEY] = self.serialize()

    @classmethod
    def from_session(cls, request):
        location = None
        str_data = request.session.get(settings.LOCATION_SESSION_KEY)
        if str_data:
            try:
                location = cls.deserialize(str_data)
            except LocationDeserializationError:
                pass
        return location

    @classmethod
    def clear_session(cls, request):
        try:
            del request.session[settings.LOCATION_SESSION_KEY]
        except KeyError:
            pass
    
    def serialize(self):
        "Serialize location to JSON."
        return serializers.serialize('json', [self])
        
    @classmethod
    def deserialize(cls, str_data):
        "Generate location from JSON output of serialize()."
        try:
            location = list(
                serializers.deserialize('json', str_data))[0].object
        except Exception as e:
            raise LocationDeserializationError(*e.args)
        return location

    def clone(self):
        return Location.deserialize(self.serialize())
