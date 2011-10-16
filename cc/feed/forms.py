from datetime import datetime

from django import forms

from cc.feed.models import FeedItem

# Passing no radius => use default, so need a code for infinite.
INFINITE_RADIUS = -1

RADIUS_CHOICES = (
    (1000, 'Within 1 km'),
    (5000, 'Within 5 km'),
    (10000, 'Within 10 km'),
    (50000, 'Within 50 km'),
    (INFINITE_RADIUS, 'Anywhere'),
)

DEFAULT_RADIUS = 5000
DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

class FeedFilterForm(forms.Form):
    d = forms.DateTimeField(
        label="Up to date", required=False, input_formats=[DATE_FORMAT])
    q = forms.CharField(
        label="Search", required=False, widget=forms.TextInput(
            attrs={'class': 'instruction_input', 'help': "Search"}))
    radius = forms.TypedChoiceField(
        required=False, choices=RADIUS_CHOICES, coerce=int, empty_value=None)
    trusted = forms.BooleanField(required=False)
    
    def __init__(self, data, profile, location=None, item_type=None,
                 poster=None, recipient=None, *args, **kwargs):
        self.profile, self.location, self.item_type = (
            profile, location, item_type)
        self.poster, self.recipient = poster, recipient
        data = data.copy()
        data.setdefault(
            'radius', profile and profile.settings.feed_radius or DEFAULT_RADIUS)
        if profile and 'q' not in data:  # Ie, form not submitted.
            # Checkbox value isn't in data when unchecked, so only set it
            # when the feed filter form hasn't been submitted.
            data.setdefault('trusted', bool(profile.settings.feed_trusted))
        super(FeedFilterForm, self).__init__(data, *args, **kwargs)

    @property
    def continued(self):
        return 'd' in self.data
        
    def get_results(self):
        data = self.cleaned_data
        date = data.get('d') or datetime.now()
        tsearch = data.get('q')
        radius = data['radius']
        query_radius = radius
        if radius == INFINITE_RADIUS:
            query_radius = None
        trusted = data['trusted']
        return FeedItem.objects.get_feed_and_remaining(
            self.profile, location=self.location, tsearch=tsearch,
            radius=query_radius, item_type=self.item_type,
            trusted_only=trusted, up_to_date=date,
            poster=self.poster, recipient=self.recipient)
        
    def update_sticky_prefs(self):
        """
        Save radius and trusted as sticky prefs to profile.
        Do this after getting feed results, because saving profile actually
        creates a new feed item for the profile, excluding it from the query
        above because it is contained in a transaction.
        """
        if not self.profile:
            return
        data = self.cleaned_data
        radius = data['radius']
        trusted = data['trusted']        
        save_settings = False
        if radius != self.profile.settings.feed_radius:
            self.profile.settings.feed_radius = radius
            save_settings = True
        if trusted != self.profile.settings.feed_trusted:
            self.profile.settings.feed_trusted = trusted
            save_settings = True
        if save_settings:
            self.profile.settings.save()
    
