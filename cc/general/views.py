"Generally useful view functions."

from django.shortcuts import render
from django.http import HttpResponseForbidden

def forbidden(request):
    return render(request, 'forbidden.html',
                  status=HttpResponseForbidden.status_code)
    
