import os
import Image

from django import template

from mediagenerator.utils import media_url

register = template.Library()

@register.filter
def resize(file, size):
    """
    Image resizing/caching filter.
    Adapted from http://www.djangosnippets.org/snippets/955/.
    """
    if not file:
        return ''
    x, y = [int(x) for x in size.split('x')]
    filehead, filetail = os.path.split(file.path)
    basename, format = os.path.splitext(filetail)
    miniature = basename + '_' + size + format
    filename = file.path
    miniature_filename = os.path.join(filehead, 'resized/', miniature)
    filehead, filetail = os.path.split(file.url)
    miniature_url = os.path.join(filehead, 'resized/', miniature)

    # Delete resized file if it is older than original.
    if (os.path.exists(miniature_filename) and
        os.path.getmtime(filename) > os.path.getmtime(miniature_filename)):
        os.unlink(miniature_filename)
        
    # Resize if no resized version already exists.
    if not os.path.exists(miniature_filename):
        # Make sure resized directory exists.
        try:
            os.makedirs(os.path.split(miniature_filename)[0])
        except OSError:
            pass
        image = Image.open(filename)
        image.thumbnail([x, y], Image.ANTIALIAS)
        try:
            image.save(miniature_filename, image.format, quality=90, optimize=1)
        except:
            image.save(miniature_filename, image.format, quality=90)

    return miniature_url

@register.filter
def default_img(original, default):
    if original:
        return original
    return media_url(default)
    
