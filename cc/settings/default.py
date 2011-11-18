# Django settings.

import os
from datetime import timedelta

ROOT_PATH = os.path.split(os.path.dirname(__file__))[0]

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Ryan Fugger', 'info@villages.cc'),
)

MANAGERS = ADMINS

SITE_DOMAIN = 'villages.cc'
DEFAULT_FROM_EMAIL = 'web@villages.cc'
HELP_EMAIL = 'info@villages.cc'
EMAIL_SUBJECT_PREFIX = "[Villages] "

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
STATIC_ROOT = os.path.join(ROOT_PATH, '../static/')

# URL that handles the static files served from STATIC_ROOT.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(ROOT_PATH, '../uploads/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/uploads/'

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
    'cc.profile.middleware.ProfileMiddleware',
    'cc.geo.middleware.LocationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'cc.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'cc.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # 'django.contrib.admindocs',
    'django.contrib.gis',
    'django.contrib.humanize',
    
    'south',
    'mediagenerator',

    'cc.geo',
    'cc.profile',
    'cc.post',
    'cc.feed',
    'cc.relate',
    'cc.general',
    'cc.pages',
    'cc.admin',
    
    # Ripple
    'cc.account',
    'cc.payment',

    # This goes below cc.admin, so cc.admin's templates are used first.
    'django.contrib.admin',
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'WARNING',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request':{
            'handlers': ['mail_admins'],
            'level': 'WARNING',
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
    ('common.js',
     'js/common.js',
     ),
    ('geo.js',
     'js/geo.js',
     ),
    ('ui.spinner.js',
     'js/ui.spinner.min.js'),
    ('ui.spinner.css',
     'css/ui.spinner.css'),
)

LOGIN_URL = '/login/'
AUTH_PROFILE_MODULE = 'profile.Profile'
LOGIN_REDIRECT_URL = '/'  # Default place to redirect after login.

AUTHENTICATION_BACKENDS = (
    'cc.profile.auth_backends.CaseInsensitiveModelBackend',
)

SESSION_COOKIE_SECURE = True
LOCATION_COOKIE_NAME = 'location_id'
LOCATION_COOKIE_AGE = timedelta(days=365)

GEOIP_PATH = '/usr/share/GeoIP'

LOCATION_SESSION_KEY = 'location_id'
DEFAULT_LOCATION = ('49.2696243', '-123.0696036')  # East Vancouver.

# Extra hearts per endorsement received.
ENDORSEMENT_BONUS = 5

FEED_ITEMS_PER_PAGE = 20

DATABASE_ROUTERS = ('cc.ripple.router.RippleRouter',)

# Testing.
TEST_RUNNER = 'cc.general.tests.AdvancedTestSuiteRunner'
TEST_PACKAGES = ['cc']
