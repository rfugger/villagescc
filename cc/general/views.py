"Generally useful view functions."

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME

def forbidden(request):
    """
    Redirect to login screen if not authenticated, otherwise display
    forbidden message.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?%s=%s' % (
                reverse('login'), REDIRECT_FIELD_NAME, request.path)) 
    else:
        return render(request, 'forbidden.html',
                      status=HttpResponseForbidden.status_code)
    
