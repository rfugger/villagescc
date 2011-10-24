from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME

def location_required(view_func):
    """
    View decorator that requires request.location to be set.
    If no session location yet, get default from request.user,
    or else redirect to locator view.
    """

    # TODO: Don't just redirect to locator view when there's no
    # location, autodetect from IP and browser and set session location
    # in cookie.  Use default names from geocoding.
    # Have separate decorator home_location_required for when we
    # need the name of the location?

    def decorated_func(request, *args, **kwargs):
        if not request.location:
            return HttpResponseRedirect("%s?%s=%s" % (
                    reverse('locator'), REDIRECT_FIELD_NAME, request.path))
        return view_func(request, *args, **kwargs)
    return decorated_func
    
