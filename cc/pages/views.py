from django.shortcuts import redirect
from django.contrib import messages

from cc.general.util import render
from cc.pages.forms import AnonymousFeedbackForm, UserFeedbackForm

MESSAGES = {
    'feedback_sent': "Thank you for your feedback.",
}

@render()
def intro(request):
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
            
