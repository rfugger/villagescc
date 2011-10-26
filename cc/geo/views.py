from django.contrib.gis.utils import GeoIP
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.conf import settings

from cc.general.util import render, get_remote_ip
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
    hide_set_home = profile is None
    get_browser_location = True
    # Work on a copy of profile location, since it is modified by
    # form validation.
    instance = profile and profile.location and profile.location.clone()
    # Don't overwrite old location -- old posts, etc., still need it.
    if instance:
        instance.id = None
    if request.method == 'POST':
        form = LocationForm(
            request.POST, instance=instance, hide_set_home=hide_set_home)
        if form.is_valid():
            if 'clear' in request.POST:
                Location.clear_session(request)
                return redirect_after_locator(request)
            save = (profile and (profile.location is None or
                                 form.cleaned_data.get('set_home', False)))
            location = form.save(commit=save)
            if save:
                profile.location = location
                profile.set_updated()
                profile.save()
                Location.clear_session(request)
            else:
                location.to_session(request)
            messages.info(request, MESSAGES['location_set'])
            return redirect_after_locator(request)
        else:
            get_browser_location = False

            # TODO: Set initial_lat, initial_lng for map redisplay.
            # Don't reset text fields in form though...

    else:
        form = LocationForm(instance=instance, hide_set_home=hide_set_home)
        if request.location:

            # TODO: Don't overwrite initial form data with geocoding javascript.
            
            initial_lng, initial_lat = request.location.point.tuple
        else:
            # Do an IP geocode as a rough first guess.
            initial_lat, initial_lng = get_geoip_coords(request)
            if initial_lat == '' or initial_lng == '':
                initial_lat, initial_lng = settings.DEFAULT_LOCATION
    return locals()

def redirect_after_locator(request):
    next = request.GET.get('next')
    if next and ':' not in next:  # Local redirects only -- no 'http://...'.
        return HttpResponseRedirect(next)
    return redirect('feed')
    
def get_geoip_coords(request):
    lat, lng = '', ''
    geoip = GeoIP()
    # TODO: Middleware to set REMOTE_ADDR from HTTP_X_FORWARDED_FOR.
    remote_addr = get_remote_ip(request)
    geoip_result = geoip.city(remote_addr)
    if geoip_result:
        lat = geoip_result.get('latitude', '')
        lng = geoip_result.get('longitude', '')
    return lat, lng
    
