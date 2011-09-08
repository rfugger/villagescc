#!/usr/bin/env python
"""
Clear out all the trusted_profiles M2M field and recreate it from the
endorsement database.
"""

from cc.relate.models import Endorsement

Endorsement.objects.rebuild_trust_network()
