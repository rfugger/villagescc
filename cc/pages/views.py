from django.shortcuts import redirect
from django.contrib import messages
from django import http
from django.template import loader, Context
from django.conf import settings

from cc.general.util import render
from cc.pages.forms import AnonymousFeedbackForm, UserFeedbackForm

MESSAGES = {
    'feedback_sent': "Thank you for your feedback.",
}

@render()
def intro(request):
    # Let logged-in users see the intro page if there's a GET param.
    if request.profile and not request.GET:
        return redirect('feed')
    return {}

@render()
def feedback(request):
    if request.method == 'POST':
        if request.profile:
            form = UserFeedbackForm(request.profile, request.POST)
        else:
            form = AnonymousFeedbackForm(request.POST)
        if form.is_valid():
            form.send()
            messages.info(request, MESSAGES['feedback_sent'])
            return redirect('home')
    else:
        if request.profile:
            form = UserFeedbackForm(request.profile)
        else:
            form = AnonymousFeedbackForm()
    return locals()

def server_error(request):
    "Renders server error view for unhandled exceptions."
    # Don't render this in regular base template, or using RequestContext,
    # because we can't count on the database (or anything really) working.
    #
    # Can't use default server_error view because it doesn't pass help_email.
    t = loader.get_template('500.html')
    c = Context({'help_email': settings.HELP_EMAIL})
    return http.HttpResponseServerError(t.render(c))
