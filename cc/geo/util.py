from datetime import datetime

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from cc.geo.models import Location, LocationDeserializationError

def location_required(view_func):
    """
    View decorator that requires request.location to be set.
    If no session location yet, get default from request.user,
    or else redirect to locator view.
    """

    # TODO: Don't just redirect to locator view when there's no
    # location, autodetect from IP and browser.  Use the default
    # geocoding.

    def decorated_func(request, *args, **kwargs):
        if not request.location and request.profile:
            location = request.profile.location
            if location:
                location.set_current(request)
        if not request.location:
            return HttpResponseRedirect(
                "%s?next=%s" % (reverse('locator'), request.path))
        return view_func(request, *args, **kwargs)
    return decorated_func

def set_location_cookie(response, loc_data):
    """
    Doesn't go in the Django session because that gets flushed on
    login/logout, and we want current location to persist through
    login/logout.
    """
    response.set_cookie(
        settings.LOCATION_COOKIE_NAME,
        value=loc_data,
        expires=datetime.now() + settings.LOCATION_COOKIE_AGE,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=settings.SESSION_COOKIE_HTTPONLY)
    
def get_location_from_cookie(request):
    location = None
    loc_data = request.COOKIES.get(settings.LOCATION_SESSION_KEY)
    if loc_data:
        try:
            location = Location.deserialize(loc_data)
        except LocationDeserializationError:  # Ignore corrupted cookie data.
            pass
    return location
    
