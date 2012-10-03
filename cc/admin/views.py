from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from cc.general.util import render
from cc.admin.forms import EmailUsersForm

@staff_member_required
@render()
def email_users(request):
    if request.method == 'POST':
        form = EmailUsersForm(request.POST)
        if form.is_valid():
            sent_count = form.send()
            messages.info(
                request, _("Email sent to %d subscribed users.") % sent_count)
            return redirect('admin:index')
    else:
        form = EmailUsersForm()
    return locals()

