from django.shortcuts import redirect

from cc.general.util import render

@render()
def intro(request):
    if request.profile:
        return redirect('feed')
    return {}
