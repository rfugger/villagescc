from django.shortcuts import redirect

from cc.general.util import render

@render()
def intro(request):
    if request.profile and not request.GET:
        return redirect('feed')
    return {}
