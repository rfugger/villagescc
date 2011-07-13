from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

MESSAGES = {
    'set_home': "Please set your home location.",
}

def profile_location_required(view_func):
    """
    Decorator that requires logged-in user to have a location set in their
    profile. If not, redirects to location chooser page with message to please
    set a home location.

    Assumes an authenticated user.  To ensure this, use after @login_required.
    """
    def decorated_func(request, *args, **kwargs):
        if not request.profile.location:
            messages.info(request, MESSAGES['set_home'])
            return HttpResponseRedirect('%s?home=1&next=%s' % (
                    reverse('locator'), request.path))
        return view_func(request, *args, **kwargs)
    return decorated_func
