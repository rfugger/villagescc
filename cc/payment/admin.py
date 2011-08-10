from django.contrib import admin

from cc.payment.models import Payment, Entry

admin.site.register(Payment)
admin.site.register(Entry)
