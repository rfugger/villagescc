"""
Ripple API module.

Also general module for stuff shared between Ripple apps account and payment.
These should be kept isolated as much as possible from the rest of the
project, so they are easier to replace by an external Ripple server.

All access to Ripple functionality should be through this module.

Notes:

* Node aliases are profile IDs.

"""

PRECISION = 12  # Digits to store.
SCALE = 2  # Decimal places to reserve.
