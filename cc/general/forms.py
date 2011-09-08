from django import forms

# *** HACK ALERT ***
# Monkeypatch forms.CharField so it strips off leading/trailing whitespace.
# Import this module from somewhere like models to be sure the patch is loaded.

def strip_result(func):
    def decorated_func(*args, **kwargs):
        return func(*args, **kwargs).strip()
    decorated_func.__name__ = func.__name__
    decorated_func.__module__ == func.__module__
    return decorated_func

forms.CharField.clean = strip_result(forms.CharField.clean)
