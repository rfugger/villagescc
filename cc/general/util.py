"General utilities."

from django.shortcuts import render as django_render, redirect

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

    The render decorator passes any extra keyword parameters, such as 'status',
    to django.shortcuts.render.
        
    To select another template to render from the view function itself,
    return a tuple of the usual response, paired with the desired template.
    """
    def __init__(self, template=None, **render_kwargs):
        self.template = template
        self.render_kwargs = render_kwargs
    
    def __call__(self, view_func):
        def decorated_func(request, *args, **kwargs):
            if self.template is None:
                self.template = '%s.html' % view_func.__name__
            result = view_func(request, *args, **kwargs)
            if isinstance(result, tuple):
                result, self.template = result
            if isinstance(result, dict):
                response = django_render(
                    request, self.template, result, **self.render_kwargs)
            else:
                response = result
            return response
        decorated_func.__name__ = view_func.__name__
        decorated_func.__module__ = view_func.__module__
        return decorated_func

def cache_on_object(accessor_func):
    def decorated_func(obj):
        cached_attr = '_cached_%s' % accessor_func.__name__
        if hasattr(obj, cached_attr):
            return getattr(obj, cached_attr)
        val = accessor_func(obj)
        setattr(obj, cached_attr, val)
        return val
    decorated_func.__name__ = accessor_func.__name__
    decorated_func.__module__ = accessor_func.__module__
    return decorated_func
            
def deflect_logged_in(view_func):
    "Redirect logged-in users to home to prevent them from using this view."
    def decorated_func(request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('home')
        return view_func(request, *args, **kwargs)
    decorated_func.__name__ = view_func.__name__
    decorated_func.__module__ = view_func.__module__
    return decorated_func
    
def get_remote_ip(request):
    "Get the original client IP address."
    return request.META.get('HTTP_X_FORWARDED_FOR', request.META['REMOTE_ADDR'])
