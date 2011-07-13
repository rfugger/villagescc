class ProfileMiddleware(object):
    def process_request(self, request):
        "Populate request with user profile, for convenience."
        if request.user.is_authenticated():
            request.profile = request.user.get_profile()
        else:
            request.profile = None
