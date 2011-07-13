from cc.geo.util import (
    get_location_from_cookie, set_location_cookie)

class LocationMiddleware(object):
    def process_request(self, request):
        """
        Set request.location to the current location if it is present
        as a location cookie, otherwise set request.location to None.
        """
        request.location = get_location_from_cookie(request)

    @classmethod
    def set_current_location(cls, request, location):
        "Change current session location."
        request.location = location
        # Set a flag attribute in request which will be detected in
        # process response and used to set the location cookie.
        request.set_location_cookie = location.serialize()
        
    def process_response(self, request, response):
        """
        Check for 'set_location_cookie' attribute in request, and set the
        session location cookie appropriately if present.
        This special attribute is set in set_current_location().
        """
        loc_data = getattr(request, 'set_location_cookie', None)
        if loc_data:
            set_location_cookie(response, loc_data)
        return response
