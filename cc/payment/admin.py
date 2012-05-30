from django.contrib import admin

from cc.payment.models import Payment, Entry

class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payer_name',
        'recipient_name',
        'amount',
        'submitted_at',
        'last_attempted_at',
        'status',
    )
    list_filter = ('status',)
    ordering = ('-submitted_at',)

    def payer_name(self, payment):
        return self._node_pretty_name(payment.payer)
    
    def recipient_name(self, payment):
        return self._node_pretty_name(payment.recipient)

    def _node_profile(self, node):
        from cc.profile.models import Profile
        try:
            return Profile.objects.get(pk=node.alias)
        except Profile.DoesNotExist:
            return None

    def _node_pretty_name(self, node):
        profile = self._node_profile(node)
        return profile and unicode(profile) or unicode(node)
        
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Entry)
