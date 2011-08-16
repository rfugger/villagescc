from cc.geo.models import Location

class LocationMiddleware(object):
    def process_request(self, request):
        """
        Set request.location to the current session location if it is
        present, to the profile location if it is not.
        """
        location = Location.from_session(request)
        if not location and request.profile:
            location = request.profile.location
        request.location = location
            
