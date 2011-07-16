# Django settings.

import os
from datetime import timedelta

ROOT_PATH = os.path.split(os.path.dirname(__file__))[0]

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Ryan Fugger', 'arv@ryanfugger.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Vancouver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds static files.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ROOT_PATH, 'static/')

# URL that handles the static files served from STATIC_ROOT.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'uploads/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = os.path.join(STATIC_URL, 'uploads/')

# URL prefix for admin media -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, 'admin/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'uhgdro=&vs^nml1u$9k!159rq3u^bp(wd)_8nax-d^2%=9ndrp'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(ROOT_PATH, 'templates'),
)

MIDDLEWARE_CLASSES = (
    # Media middleware has to come first (serves dev media).
    'mediagenerator.middleware.MediaMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'cc.geo.middleware.LocationMiddleware',
    'cc.profile.middleware.ProfileMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'cc.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # 'django.contrib.admindocs',

    'south',
    'mediagenerator',

    'cc.geo',
    'cc.profile',
    'cc.endorse',
    'cc.post',
    'cc.feed',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    # Removed 'static' processor because mediagenerator handles it.
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request':{
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Media generator settings.
DEV_MEDIA_URL = STATIC_URL
PRODUCTION_MEDIA_URL = STATIC_URL 
MEDIA_DEV_MODE = DEBUG
GLOBAL_MEDIA_DIRS = (STATIC_ROOT,)

MEDIA_BUNDLES = (
    ('content.css',
     'css/init.css',
     'css/template.css',
     'css/grids.css',
     'css/content.scss',
     ),
    ('geo.js',
     'js/geo.js',
     ),
)

LOGIN_URL = '/login/'
AUTH_PROFILE_MODULE = 'profile.Profile'
LOGIN_REDIRECT_URL = '/'  # Default place to redirect after login.

SESSION_COOKIE_SECURE = True
LOCATION_COOKIE_NAME = 'location_id'
LOCATION_COOKIE_AGE = timedelta(days=365)

# GeoIP.
GEOIP_PATH = '/usr/share/GeoIP'

# Geo stuff.
LOCATION_SESSION_KEY = 'location_id'
DEFAULT_LOCATION = ('49.248523', '-123.108')  # Vancouver.

INITIAL_ENDORSEMENTS = 5
