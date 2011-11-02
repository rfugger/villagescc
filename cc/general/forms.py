from django import forms

# *** HACK ALERT ***
# Monkeypatch some form things so the defaults are nicer:
# Import this module from somewhere like models to be sure the patch is loaded.

# Monkeypatch forms.CharField so it strips off leading/trailing whitespace
# on input to clean() before it is processed.  (Validation will fail if only
# whitespace is input into required fields.)
def strip_input(func):
    def decorated_func(self, value):
        if isinstance(value, basestring):
            value = value.strip()
        return func(self, value)
    decorated_func.__name__ = func.__name__
    decorated_func.__module__ == func.__module__
    return decorated_func

forms.CharField.clean = strip_input(forms.CharField.clean)

# Set required rows to class="required".
forms.BaseForm.required_css_class = "required"
