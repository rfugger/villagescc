from datetime import datetime

from django import forms
from django.conf import settings

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

RADII = [rc[0] for rc in RADIUS_CHOICES]
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
                 poster=None, recipient=None, do_filter=False, *args, **kwargs):
        self.profile, self.location, self.item_type = (
            profile, location, item_type)
        self.poster, self.recipient = poster, recipient
        data = data.copy()
        if do_filter and 'radius' not in data:
            default_radius = (profile and profile.settings.feed_radius
                              or DEFAULT_RADIUS)
            data['radius'] = default_radius
            self._explicit_radius = False
        else:
            self._explicit_radius = True
        if do_filter and 'q' not in data:  # Fresh load, no search/filter.
            # Set trusted checkbox to the profile sticky setting.
            # Can't just check for presence of 'trusted' in data, because
            # it is not submitted when unchecked.
            if profile:
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

        while True:
            items, count = FeedItem.objects.get_feed_and_remaining(
                self.profile, location=self.location, tsearch=tsearch,
                radius=query_radius, item_type=self.item_type,
                trusted_only=trusted, up_to_date=date,
                poster=self.poster, recipient=self.recipient)
            # On first or anonymous visits without explicit radius, expand radius
            # until there are a bunch of items or until we're at max radius.

            # TODO, WORKING ON: Test this out... *************************
            
            if (not (self.profile and self.profile.settings.feed_radius) and
                not self._explicit_radius and
                len(items) < settings.FEED_ITEMS_PER_PAGE and
                query_radius != None):
                query_radius = next_query_radius(query_radius)
                self.data['radius'] = query_radius
                if query_radius == INFINITE_RADIUS:
                    query_radius = None
                continue
            break
        return items, count
        
    def update_sticky_filter_prefs(self):
        """
        Save radius and trusted filter values as sticky prefs to profile
        settings.
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
    
def next_query_radius(radius):
    i = RADII.index(radius)
    return RADII[i + 1]
