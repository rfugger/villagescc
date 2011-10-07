from django import forms

# *** HACK ALERT ***
# Monkeypatch forms.CharField so it strips off leading/trailing whitespace
# on input to clean() before it is processed.  (Validation will fail if only
# whitespace is input into required fields.)
#
# Import this module from somewhere like models to be sure the patch is loaded.

def strip_input(func):
    def decorated_func(self, value):
        return func(self, value and value.strip() or value)
    decorated_func.__name__ = func.__name__
    decorated_func.__module__ == func.__module__
    return decorated_func

forms.CharField.clean = strip_input(forms.CharField.clean)
