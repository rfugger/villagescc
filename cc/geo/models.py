from django.contrib.gis.db import models
from django.core import serializers
from django.core.serializers.base import DeserializationError

from cc.general.models import VarCharField

class LocationDeserializationError(Exception):
    pass

class Location(models.Model):
    "A geographic location, named by neighborhood, city, state, country."
    # TODO: Investigate using geometry instead of geography here for better
    # performance:
    # http://postgis.refractions.net/documentation/manual-1.5/ch04.html#PostGIS_GeographyVSGeometry
    point = models.PointField(geography=True)
    country = VarCharField()
    state = VarCharField("State/Province", blank=True)  # Store as abbreviation.
    city = VarCharField(blank=True)
    neighborhood = VarCharField(blank=True)
    
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

    def set_current(self, request):
        "Makes this location the current location for this session."
        from cc.geo.middleware import LocationMiddleware
        LocationMiddleware.set_current_location(request, self)
    
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
