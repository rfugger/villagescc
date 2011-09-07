from django import forms

from cc.feed.models import FeedItem

# TODO: Move these constants to settings?
RADIUS_CHOICES = (
    (1000, '1 km'),
    (5000, '5 km'),
    (10000, '10 km'),
    (50000, '50 km'),
    (-1, 'Anywhere'),
)

DEFAULT_RADIUS = 5000

class FeedFilterForm(forms.Form):
    p = forms.IntegerField(label="Page", required=False, min_value=1)
    q = forms.CharField(
        label="Search", required=False, widget=forms.TextInput(
            attrs={'class': 'instruction_input', 'help': "Search"}))
    radius = forms.TypedChoiceField(
        required=False, choices=RADIUS_CHOICES, coerce=int, empty_value=None)
    trusted = forms.BooleanField(required=False)

    def __init__(self, data, profile, *args, **kwargs):
        data = data.copy()
        data.setdefault('radius', profile.feed_radius or DEFAULT_RADIUS)
        if 'q' not in data:  # Ie, form not submitted.
            # Checkbox value isn't in data when unchecked, so only set it
            # when the feed filter form hasn't been submitted.
            data.setdefault('trusted', bool(profile.feed_trusted))
        super(FeedFilterForm, self).__init__(data, *args, **kwargs)
    
    def get_results(self, profile, location, item_type):
        data = self.cleaned_data
        page = data.get('p') or 1
        tsearch = data.get('q')
        radius = data['radius']
        if radius != profile.feed_radius:
            profile.feed_radius = radius
            profile.save()
        trusted = data['trusted']
        if trusted != profile.feed_trusted:
            profile.feed_trusted = trusted
            profile.save()
        if radius == -1:
            radius = None
        return FeedItem.objects.get_feed(
            profile, location, page=page, tsearch=tsearch, radius=radius,
            item_type=item_type)
        
