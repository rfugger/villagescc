"General utilities."

from django.shortcuts import render as django_render

class render(object):
    """
    Decorator that allows a view function to just return a dict,
    which is used to populate a RequestContext, and render the
    template passed to the decorator.  If no template is passed,
    render tries to use name of the view function + '.html'.

    If the return value from the view is not a dict, then that
    value is returned as-is.

    Usage:
    
    @render('template.html')
    def view_func(request):
        return {'key': value}

    To select another template to render from the view function itself,
    return a tuple of the usual response, paired with the desired template.
    """
    def __init__(self, template=None):
        self.template = template
    
    def __call__(self, view_func):
        def decorated_func(request, *args, **kwargs):
            if self.template is None:
                self.template = '%s.html' % view_func.__name__
            result = view_func(request, *args, **kwargs)
            if isinstance(result, tuple):
                result, self.template = result
            if isinstance(result, dict):
                response = django_render(request, self.template, result)
            else:
                response = result
            return response
        decorated_func.__name__ = view_func.__name__
        decorated_func.__module__ = view_func.__module__
        return decorated_func

