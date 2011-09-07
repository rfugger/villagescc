#!/usr/bin/env python
"""
Clear out all the trusted_profiles M2M field and recreate it from the
endorsement database.
"""

from cc.profile.models import Profile
from cc.relate.models import Endorsement

for profile in Profile.objects.all():
    profile.trusted_profiles.clear()

for endorsement in Endorsement.objects.all():
    endorsement.update_trust_network()
