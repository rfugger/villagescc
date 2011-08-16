from django.contrib.gis.utils import GeoIP
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.conf import settings

from cc.general.util import render
from cc.geo.forms import LocationForm
from cc.geo.models import Location

MESSAGES = {
    'location_set': "Location set.",
}

@render()
def locator(request):
    """
    Renders and processes user location chooser form.
    Can be used to set either current session location, or default home
    location.
    When changing home location, existing location is updated in DB,
    so any posts using that location get their location modified as well.
    """
    profile = request.profile
    # Work on a copy of profile location, since it is modified by
    # form validation.
    instance = profile and profile.location and profile.location.clone()
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=instance)
        if form.is_valid():
            save = (profile and (profile.location is None or
                                 form.cleaned_data['set_home']))
            location = form.save(commit=save)
            if save:
                profile.location = location
                profile.save()
                Location.clear_session(request)
            else:
                location.to_session(request)
            messages.info(request, MESSAGES['location_set'])
            next = request.GET.get('next')
            if next and ':' not in next:  # Local redirects only -- no 'http://...'.
                return HttpResponseRedirect(next)
            return redirect('home')
        else:
            
            # TODO: Set initial_lat, initial_lng for map redisplay.
            # Don't reset text fields in form though...
            # Also, don't ask for browser location again.

            pass
    else:
        form = LocationForm(instance=instance)
        if request.location:

            # TODO: Don't overwrite initial form data with geocoding javascript.
            
            initial_lng, initial_lat = request.location.point.tuple
        else:
            # Do an IP geocode as a rough first guess.
            initial_lat, initial_lng = get_geoip_coords(request)
            if initial_lat == '' or initial_lng == '':
                initial_lat, initial_lng = settings.DEFAULT_LOCATION
    get_browser_location = request.location is None
    return locals()

def get_geoip_coords(request):
    lat, lng = '', ''
    geoip = GeoIP()
    # TODO: Middleware to set REMOTE_ADDR from HTTP_X_FORWARDED_FOR.
    remote_addr = request.META['REMOTE_ADDR']
    if remote_addr == '127.0.0.1':
        remote_addr = '174.6.82.184'  # For dev on localhost.
    geoip_result = geoip.city(remote_addr)
    if geoip_result:
        lat = geoip_result.get('latitude', '')
        lng = geoip_result.get('longitude', '')
    return lat, lng
    
