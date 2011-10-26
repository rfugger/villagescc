from cc.profile.models import Profile

class ProfileMiddleware(object):
    def process_request(self, request):
        "Populate request with user profile, for convenience."
        request.profile = None
        if request.user.is_authenticated():
            try:
                request.profile = request.user.profile
            except Profile.DoesNotExist:
                pass

